from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .catalog import PRODUCTS, PARTNERS, Product, Partner


CONFIDENCE_AUTO = 0.82
CONFIDENCE_REVIEW = 0.55


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = text.replace("ß", "ss")
    text = re.sub(r"[^a-z0-9:+]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "from", "please", "need", "want", "order",
        "quote", "angebot", "bestellung", "bitte", "wir", "und", "fur", "von",
        "eine", "einen", "der", "die", "das", "kg", "g", "pack", "packs",
        "stck", "stuck", "pcs", "pc", "x", "of", "our", "unsere", "unser",
    }
    return {t for t in normalize(text).split() if t not in stop and len(t) > 1}


@dataclass
class ExtractedLine:
    raw: str
    sku: str | None
    product_name: str | None
    qty: int
    uom: str | None
    unit_price: float | None
    confidence: float
    match_reason: str
    issues: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    partner_id: str | None
    partner_name: str | None
    partner_confidence: float
    intent: str
    language: str
    requested_delivery: str | None
    notes: str
    lines: list[ExtractedLine]
    overall_confidence: float
    needs_review: bool
    review_reasons: list[str]
    estimated_cost_eur: float


ORDER_UOM = r"(?:stk|stck|stuck|stucke|pcs|pc|bags?|tubs?|dosen?|flaschen?|bottles?|kartons?|cartons?|packs?|units?)?"
PRODUCT_KW = (
    "whey", "protein", "creatin", "kreatin", "omega", "vitamin", "magnesium",
    "kollagen", "collagen", "bcaa", "pre-workout", "pre workout", "preworkout",
    "erbsen", "riegel", "bar", "booster", "molke", "isolat", "shake", "dosen",
)
SKIP_LINE = re.compile(
    r"^(hallo|hi\b|hey\b|guten |danke|vielen|liebe |mit freundlichen|bitte netto|"
    r"zahlung|liefertermin|lieferung bis|lieferung kw|lieferung nach|unterschrift|"
    r"kunde:|company:|rfq\b|quotation request|need delivery|thanks|asap please|"
    r"bitte auf unser|bitte staffel|need prices)",
    re.I,
)
INFORMAL = re.compile(
    r"\b(irgendwie|egal welche|mal schnell|könnt ihr|sagen wir|substitute|ersatz|"
    r"staffelpreis|private label|recovery shake)\b",
    re.I,
)


def detect_language(text: str) -> str:
    de_hits = len(re.findall(r"\b(bitte|angebot|bestellung|lieferung|stuck|möchten|mochten|unsere|vielen|dank)\b", text, re.I))
    en_hits = len(re.findall(r"\b(please|quote|order|delivery|need|thanks|could|would)\b", text, re.I))
    return "de" if de_hits >= en_hits else "en"


def detect_intent(text: str) -> str:
    t = normalize(text)
    quote_words = ("quote", "angebot", "quotation", "rfq", "preis", "offer")
    order_words = ("order", "bestellung", "bestellen", "po ", "purchase order", "nachbestellung")
    q = sum(1 for w in quote_words if w in t)
    o = sum(1 for w in order_words if w in t)
    if q > o:
        return "quote"
    if o > q:
        return "order"
    if "angebot" in t or "quote" in t:
        return "quote"
    return "order"


def detect_delivery(text: str) -> str | None:
    patterns = [
        r"(?:bis|by|until|lieferung(?:stermin)?|delivery)\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
        r"(kw|week)\s*(\d{1,2})",
        r"(sofort|asap|express|dringend|urgent)",
        r"(nächste woche|next week|diese woche|this week)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(0)
    return None


def match_partner(text: str) -> tuple[Partner | None, float, str]:
    n = normalize(text)
    best: tuple[Partner | None, float, str] = (None, 0.0, "no partner match")
    for partner in PARTNERS:
        names = [partner.name, *partner.aliases]
        for name in names:
            nn = normalize(name)
            if nn and nn in n:
                score = 0.97 if name == partner.name else 0.9
                if score > best[1]:
                    best = (partner, score, f"matched '{name}'")
        if partner.email.lower() in text.lower():
            if 0.99 > best[1]:
                best = (partner, 0.99, "matched sender email")
        if partner.city and normalize(partner.city) in n and best[1] < 0.55:
            best = (partner, 0.52, f"weak city match {partner.city}")
    return best


def score_product(item_text: str, product: Product) -> float:
    item_n = normalize(item_text)
    names = [product.name, product.name_de, product.sku.lower(), *product.aliases]
    best = 0.0
    for name in names:
        nn = normalize(name)
        if not nn:
            continue
        if nn == item_n:
            best = max(best, 0.99)
            continue
        if nn in item_n or item_n in nn:
            best = max(best, 0.92)
            continue
        a, b = token_set(item_text), token_set(name)
        if not a or not b:
            continue
        overlap = len(a & b) / len(a | b)
        if overlap >= 0.45:
            best = max(best, 0.55 + overlap * 0.4)
        sku_tail = product.sku.split("-")[-1].lower()
        if sku_tail in item_n and overlap >= 0.25:
            best = max(best, 0.7)
    if product.pack_size and normalize(product.pack_size) in item_n:
        best = min(1.0, best + 0.05)
    return min(1.0, best)


def match_product(item_text: str) -> tuple[Product | None, float, str]:
    ranked = sorted(
        ((p, score_product(item_text, p)) for p in PRODUCTS),
        key=lambda x: x[1],
        reverse=True,
    )
    top, top_score = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    if top_score < 0.5:
        return None, top_score, "no catalog match"
    if top_score - second < 0.08 and second >= 0.5:
        return top, min(top_score, 0.68), f"ambiguous vs {ranked[1][0].sku}"
    reason = "strong catalog match" if top_score >= 0.85 else "fuzzy catalog match"
    return top, top_score, reason


def looks_like_item(line: str) -> bool:
    s = line.strip()
    if len(s) < 4 or SKIP_LINE.search(s):
        return False
    if re.search(r"propose a substitute|if you have it|staffelpreis falls", s, re.I):
        if not re.search(r"\bqty\b|\bmenge\b|\d+\s*x\b", s, re.I):
            return False
    n = normalize(s)
    if any(k in n for k in PRODUCT_KW):
        return True
    if re.search(r"(item|position)\s*\d+", s, re.I):
        return True
    if re.search(r"\d+\s*(?:x|×|stk|pcs|bags|units|menge)", s, re.I):
        return True
    return False


def split_compound(line: str) -> list[str]:
    parts = [p.strip(" ,") for p in re.split(r"\s+(?:und|and)\s+", line) if p.strip()]
    if len(parts) < 2:
        return [line]
    useful = [p for p in parts if looks_like_item(p) or re.search(r"\d", p)]
    product_parts = [p for p in useful if any(k in normalize(p) for k in PRODUCT_KW)]
    if len(product_parts) >= 2:
        return product_parts
    return [line]


def split_lines(body: str) -> list[str]:
    chunks: list[str] = []
    for raw in re.split(r"[\n;•]+", body):
        line = raw.strip(" -\t")
        if not looks_like_item(line):
            continue
        chunks.extend(split_compound(line))
    if not chunks:
        chunks = [ln.strip() for ln in body.split("\n") if looks_like_item(ln)][:8]
    return chunks


def parse_qty_and_item(line: str) -> tuple[int, str]:
    raw = re.sub(r"^(?:position|item)\s*\w+\s*:?\s*", "", line.strip(), flags=re.I)
    raw = re.sub(r"\s+", " ", raw).strip(" -:.")

    m = re.match(r"^(?P<qty>\d+)\s*(?:x|×)\s+(?P<item>.+)$", raw, re.I)
    if m:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.match(
        rf"^(?P<qty>\d+)\s+{ORDER_UOM}\s+(?:of\s+)?(?P<item>.+)$",
        raw,
        re.I,
    )
    if m and m.group("item") and len(m.group("item").strip()) >= 3:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.search(r"menge\s+(?P<qty>\d+)", raw, re.I)
    if m:
        item = re.sub(r"menge\s+\d+", "", raw, flags=re.I)
        item = re.sub(r"^(?:position|item)\s*\w+\s*:?\s*", "", item, flags=re.I)
        return int(m.group("qty")), item.strip(" -:")

    m = re.match(rf"^(?P<item>.+?)\s+[–-]\s+(?P<qty>\d+)\s*{ORDER_UOM}\s*$", raw, re.I)
    if m:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.match(r"^(?P<item>.+?)\s*[:=]\s*(?P<qty>\d+)\s*$", raw, re.I)
    if m:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.match(r"^(?P<item>.+?)\s+(?:x|×)\s+(?P<qty>\d+)\s*$", raw, re.I)
    if m:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.match(rf"^(?P<item>.+?)\s+(?P<qty>\d+)\s+{ORDER_UOM}\s*$", raw, re.I)
    if m and len(m.group("item").strip()) >= 3:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.search(r"\bqty\s*[:=]?\s*(?P<qty>\d+)\s*$", raw, re.I)
    if m:
        item = raw[: m.start()].strip(" -:")
        if len(item) >= 3:
            return int(m.group("qty")), item

    m = re.match(r"^(?P<qty>\d+)\s+(?P<item>.+)$", raw)
    if m and not re.match(r"^\d+\s*(?:kg|g|iu|i\.e)", m.group("item"), re.I):
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.search(
        r"\b(?P<qty>\d+)\s+(?P<item>(?:whey|molke|kreatin|creatin|pre[\s-]?workout|booster|omega|vitamin|magnesium|kollagen|collagen|bcaa|erbsen|protein|riegel).+)$",
        raw,
        re.I,
    )
    if m:
        return int(m.group("qty")), m.group("item").strip(" -:.")

    m = re.search(r"sagen wir\s+(?P<qty>\d+)", raw, re.I)
    if m:
        item = re.sub(r"sagen wir\s+\d+", "", raw, flags=re.I)
        item = re.sub(r"irgendwie noch", "", item, flags=re.I)
        return int(m.group("qty")), item.strip(" -:,.")

    return 1, raw


def extract(subject: str, body: str, sender: str = "") -> ExtractionResult:
    full = f"{sender}\n{subject}\n{body}"
    language = detect_language(full)
    intent = detect_intent(full)
    partner, p_conf, p_reason = match_partner(full)
    delivery = detect_delivery(body) or detect_delivery(subject)

    lines: list[ExtractedLine] = []
    for raw in split_lines(body):
        qty, item = parse_qty_and_item(raw)
        product, score, reason = match_product(item)
        issues: list[str] = []
        if product is None:
            issues.append("unmatched product")
        if qty > 500:
            issues.append("unusual quantity")
            score = min(score, 0.55)
        if product and product.stock < qty:
            issues.append("stock below order qty")
        conf = round(score, 3)
        lines.append(
            ExtractedLine(
                raw=raw,
                sku=product.sku if product else None,
                product_name=(product.name if language == "en" else product.name_de) if product else None,
                qty=qty,
                uom=product.uom if product else None,
                unit_price=product.list_price if product else None,
                confidence=conf,
                match_reason=reason,
                issues=issues,
            )
        )

    review_reasons: list[str] = []
    if partner is None or p_conf < CONFIDENCE_AUTO:
        review_reasons.append("customer identity uncertain")
    if not lines:
        review_reasons.append("no line items extracted")
    blocking = [
        ln
        for ln in lines
        if ln.sku is None
        or ln.confidence < CONFIDENCE_AUTO
        or "unmatched product" in ln.issues
        or "unusual quantity" in ln.issues
    ]
    if blocking:
        review_reasons.append(f"{len(blocking)} line(s) need review")
    if any(ln.sku is None for ln in lines):
        review_reasons.append("unknown SKU")
    if INFORMAL.search(full):
        review_reasons.append("informal or substitution language")

    ident_conf = [ln.confidence for ln in lines if ln.sku]
    line_conf = min(ident_conf, default=0.0)
    overall = round(min(p_conf if partner else 0.4, line_conf if ident_conf else 0.3), 3)
    if review_reasons:
        overall = min(overall, 0.79)

    needs_review = bool(review_reasons) or overall < CONFIDENCE_AUTO
    tokens = max(180, len(full) // 4)
    cost = round(tokens / 1_000_000 * 0.40 + 0.002, 4)

    notes = p_reason
    if delivery:
        notes += f"; delivery: {delivery}"

    return ExtractionResult(
        partner_id=partner.id if partner else None,
        partner_name=partner.name if partner else None,
        partner_confidence=round(p_conf, 3),
        intent=intent,
        language=language,
        requested_delivery=delivery,
        notes=notes,
        lines=lines,
        overall_confidence=overall,
        needs_review=needs_review,
        review_reasons=review_reasons,
        estimated_cost_eur=cost,
    )
