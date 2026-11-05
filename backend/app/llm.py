from __future__ import annotations

import json
import re
from typing import Any

import httpx

from .catalog import PRODUCTS, PARTNERS, product_by_sku, partner_by_id
from .extractor import (
    CONFIDENCE_AUTO,
    ExtractedLine,
    ExtractionResult,
    detect_delivery,
    detect_intent,
    detect_language,
    extract as rules_extract,
    match_partner,
    match_product,
)
from .settings import PROVIDERS, llm_settings


def catalog_brief() -> str:
    products = "\n".join(
        f"- {p.sku} | {p.name} / {p.name_de} | {p.uom} {p.pack_size} | aliases: {', '.join(p.aliases[:4])}"
        for p in PRODUCTS
    )
    partners = "\n".join(
        f"- {p.id} | {p.name} | {p.city} | {p.email} | aliases: {', '.join(p.aliases[:3])}"
        for p in PARTNERS
    )
    return f"PRODUCTS:\n{products}\n\nCUSTOMERS:\n{partners}"


SYSTEM_PROMPT = """You extract purchase orders and quote requests for Nutrifill, a German nutritional wholesaler.
Return ONLY valid JSON with this schema:
{
  "partner_id": "P-1001 or null if unknown",
  "intent": "order" or "quote",
  "language": "de" or "en",
  "requested_delivery": "string or null",
  "notes": "short note",
  "lines": [
    {"raw": "original snippet", "sku": "NF-... or null", "qty": 1, "confidence": 0.0}
  ]
}
Rules:
- Map every requested item to a catalog SKU when possible.
- If the customer asks for an unknown product, keep sku null.
- Do not invent customers. Use partner_id from the catalog or null.
- Informal German is allowed. Quantities must be integers.
- Ignore greetings, payment terms and signatures as line items.
- confidence is 0-1 for each line.
"""


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    spec = PROVIDERS.get(llm_settings.provider, PROVIDERS["custom"])
    cost = (
        prompt_tokens / 1_000_000 * spec["input_eur_per_m"]
        + completion_tokens / 1_000_000 * spec["output_eur_per_m"]
    )
    return round(cost + 0.0001, 5)


def call_llm(subject: str, body: str, sender: str) -> tuple[dict[str, Any], float, int, int]:
    user = (
        f"Sender: {sender}\nSubject: {subject}\n\nEmail/PDF text:\n{body}\n\n"
        f"{catalog_brief()}"
    )
    url = llm_settings.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": llm_settings.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    }
    headers = {
        "Authorization": f"Bearer {llm_settings.api_key}",
        "Content-Type": "application/json",
    }
    with httpx.Client(timeout=45.0) as client:
        res = client.post(url, headers=headers, json=payload)
        if res.status_code >= 400 and "response_format" in payload:
            payload.pop("response_format", None)
            res = client.post(url, headers=headers, json=payload)
        if res.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {res.status_code}: {res.text[:300]}")
        data = res.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or max(200, len(user) // 4))
    completion_tokens = int(usage.get("completion_tokens") or max(80, len(content) // 4))
    parsed = _parse_json(content)
    return parsed, estimate_cost(prompt_tokens, completion_tokens), prompt_tokens, completion_tokens


def _hydrate_llm(parsed: dict[str, Any], subject: str, body: str, sender: str, cost: float) -> ExtractionResult:
    full = f"{sender}\n{subject}\n{body}"
    language = parsed.get("language") or detect_language(full)
    intent = parsed.get("intent") if parsed.get("intent") in {"order", "quote"} else detect_intent(full)
    partner = partner_by_id(parsed.get("partner_id") or "")
    p_conf = 0.96 if partner else 0.0
    p_reason = "llm partner" if partner else "llm did not identify customer"
    if not partner:
        partner, p_conf, p_reason = match_partner(full)

    lines: list[ExtractedLine] = []
    for raw_ln in parsed.get("lines") or []:
        raw = str(raw_ln.get("raw") or "").strip() or "item"
        qty = int(raw_ln.get("qty") or 1)
        if qty <= 0:
            qty = 1
        sku = raw_ln.get("sku")
        product = product_by_sku(sku) if sku else None
        score = float(raw_ln.get("confidence") or 0.0)
        reason = "llm catalog map"
        if product is None:
            product, score, reason = match_product(raw)
        else:
            score = max(score, 0.9)
        issues: list[str] = []
        if product is None:
            issues.append("unmatched product")
        if qty > 500:
            issues.append("unusual quantity")
            score = min(score, 0.55)
        if product and product.stock < qty:
            issues.append("stock below order qty")
        lines.append(
            ExtractedLine(
                raw=raw,
                sku=product.sku if product else None,
                product_name=(product.name if language == "en" else product.name_de) if product else None,
                qty=qty,
                uom=product.uom if product else None,
                unit_price=product.list_price if product else None,
                confidence=round(min(1.0, score), 3),
                match_reason=reason,
                issues=issues,
            )
        )

    if not lines:
        fallback = rules_extract(subject, body, sender)
        fallback.notes = (fallback.notes or "") + "; llm returned no lines"
        fallback.estimated_cost_eur = cost
        return fallback

    review_reasons: list[str] = []
    if partner is None or p_conf < CONFIDENCE_AUTO:
        review_reasons.append("customer identity uncertain")
    blocking = [
        ln
        for ln in lines
        if ln.sku is None or ln.confidence < CONFIDENCE_AUTO or "unmatched product" in ln.issues
    ]
    if blocking:
        review_reasons.append(f"{len(blocking)} line(s) need review")
    if any(ln.sku is None for ln in lines):
        review_reasons.append("unknown SKU")

    ident_conf = [ln.confidence for ln in lines if ln.sku]
    line_conf = min(ident_conf, default=0.0)
    overall = round(min(p_conf if partner else 0.4, line_conf if ident_conf else 0.3), 3)
    if review_reasons:
        overall = min(overall, 0.79)

    delivery = parsed.get("requested_delivery") or detect_delivery(body) or detect_delivery(subject)
    notes = parsed.get("notes") or p_reason
    return ExtractionResult(
        partner_id=partner.id if partner else None,
        partner_name=partner.name if partner else None,
        partner_confidence=round(p_conf, 3),
        intent=intent,
        language=language if language in {"de", "en"} else detect_language(full),
        requested_delivery=delivery,
        notes=f"llm:{llm_settings.provider}/{llm_settings.model}; {notes}",
        lines=lines,
        overall_confidence=overall,
        needs_review=bool(review_reasons) or overall < CONFIDENCE_AUTO,
        review_reasons=review_reasons,
        estimated_cost_eur=cost,
    )


def extract_document(subject: str, body: str, sender: str = "", prefer_llm: bool = False) -> ExtractionResult:
    use_llm = prefer_llm and llm_settings.enabled
    if not use_llm:
        result = rules_extract(subject, body, sender)
        result.notes = ("rules; " + (result.notes or "")).strip()
        return result
    try:
        parsed, cost, _, _ = call_llm(subject, body, sender)
        return _hydrate_llm(parsed, subject, body, sender, cost)
    except Exception as exc:
        result = rules_extract(subject, body, sender)
        result.notes = f"llm failed ({exc}); fallback rules; {result.notes}"
        result.review_reasons = list(result.review_reasons) + ["llm fallback to rules"]
        result.needs_review = True
        result.overall_confidence = min(result.overall_confidence, 0.79)
        return result
