from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from .catalog import PRODUCTS, PARTNERS
from .documents import SAMPLES, get_sample
from .extractor import ExtractionResult
from .llm import extract_document
from .metrics import score_extraction, aggregate
from .odoo_sim import build_quote, quote_to_dict
from .settings import llm_settings


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def extraction_to_dict(ext: ExtractionResult) -> dict[str, Any]:
    return {
        "partner_id": ext.partner_id,
        "partner_name": ext.partner_name,
        "partner_confidence": ext.partner_confidence,
        "intent": ext.intent,
        "language": ext.language,
        "requested_delivery": ext.requested_delivery,
        "notes": ext.notes,
        "lines": [
            {
                "raw": ln.raw,
                "sku": ln.sku,
                "product_name": ln.product_name,
                "qty": ln.qty,
                "uom": ln.uom,
                "unit_price": ln.unit_price,
                "confidence": ln.confidence,
                "match_reason": ln.match_reason,
                "issues": ln.issues,
            }
            for ln in ext.lines
        ],
        "overall_confidence": ext.overall_confidence,
        "needs_review": ext.needs_review,
        "review_reasons": ext.review_reasons,
        "estimated_cost_eur": ext.estimated_cost_eur,
    }


class Store:
    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.quotes: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self._seed()

    def _log(self, action: str, detail: str, ref: str = "") -> None:
        self.audit.insert(
            0,
            {
                "id": str(uuid4())[:8],
                "at": _now(),
                "action": action,
                "detail": detail,
                "ref": ref,
            },
        )

    def _seed(self) -> None:
        for sample in SAMPLES:
            self.ingest(
                {
                    "source": sample.source,
                    "from_name": sample.from_name,
                    "from_email": sample.from_email,
                    "subject": sample.subject,
                    "body": sample.body,
                    "sample_id": sample.id,
                    "language": sample.language,
                }
            )

    def ingest(self, payload: dict[str, Any]) -> dict[str, Any]:
        subject = payload.get("subject") or ""
        body = payload.get("body") or ""
        sender = f"{payload.get('from_name', '')} {payload.get('from_email', '')}"
        sample_id = payload.get("sample_id")
        prefer_llm = bool(payload.get("use_llm", True)) and not sample_id
        ext = extract_document(subject, body, sender, prefer_llm=prefer_llm)
        sample = get_sample(sample_id) if sample_id else None

        status = "needs_review" if ext.needs_review else "auto_quoted"
        quote = None
        if not ext.needs_review and ext.partner_id:
            items = [
                {"sku": ln.sku, "qty": ln.qty, "unit_price": ln.unit_price}
                for ln in ext.lines
                if ln.sku
            ]
            q = build_quote(
                seq=len(self.quotes),
                partner_id=ext.partner_id,
                intent=ext.intent,
                items=items,
                source_document_id=sample_id or "",
                notes=ext.notes,
            )
            quote = quote_to_dict(q)
            quote["state"] = "draft"
            self.quotes.append(quote)
            status = "draft_in_odoo"

        gold = None
        if sample:
            gold = score_extraction(sample, ext)

        job = {
            "id": f"JOB-{len(self.jobs) + 1:03d}",
            "created_at": _now(),
            "source": payload.get("source", "email"),
            "from_name": payload.get("from_name", ""),
            "from_email": payload.get("from_email", ""),
            "subject": subject,
            "body": body,
            "sample_id": sample_id,
            "language": ext.language,
            "status": status,
            "extraction": extraction_to_dict(ext),
            "quote_id": quote["id"] if quote else None,
            "reviewer_note": "",
            "gold": gold,
            "reviewed_at": None,
            "extractor": "llm" if ext.notes.startswith("llm:") else "rules",
        }
        self.jobs.insert(0, job)
        self._log("ingest", f"{job['id']} {subject[:60]}", job["id"])
        if quote:
            self._log("odoo.draft_quote", f"{quote['id']} for {quote['partner_name']}", quote["id"])
        return job

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        for j in self.jobs:
            if j["id"] == job_id:
                return j
        return None

    def review(self, job_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        job = self.get_job(job_id)
        if not job:
            return None
        ext = job["extraction"]
        if "partner_id" in payload and payload["partner_id"]:
            ext["partner_id"] = payload["partner_id"]
            from .catalog import partner_by_id

            p = partner_by_id(payload["partner_id"])
            if p:
                ext["partner_name"] = p.name
                ext["partner_confidence"] = 1.0
        if "intent" in payload and payload["intent"]:
            ext["intent"] = payload["intent"]
        if "lines" in payload and payload["lines"] is not None:
            ext["lines"] = payload["lines"]
        ext["needs_review"] = False
        ext["review_reasons"] = []
        ext["overall_confidence"] = 1.0
        job["reviewer_note"] = payload.get("note", "")
        job["reviewed_at"] = _now()

        action = payload.get("action", "approve")
        if action == "reject":
            job["status"] = "rejected"
            self._log("review.reject", job_id, job_id)
            return job

        partner_id = ext.get("partner_id")
        items = [
            {"sku": ln["sku"], "qty": ln["qty"], "unit_price": ln.get("unit_price")}
            for ln in ext["lines"]
            if ln.get("sku")
        ]
        if not partner_id or not items:
            job["status"] = "needs_review"
            return job

        q = build_quote(
            seq=len(self.quotes),
            partner_id=partner_id,
            intent=ext.get("intent") or "quote",
            items=items,
            source_document_id=job.get("sample_id") or job["id"],
            notes=job.get("reviewer_note") or ext.get("notes") or "",
        )
        quote = quote_to_dict(q)
        self.quotes.append(quote)
        job["quote_id"] = quote["id"]
        job["status"] = "draft_in_odoo"
        self._log("review.approve", f"{job_id} -> {quote['id']}", job_id)
        return job

    def set_quote_state(self, quote_id: str, state: str) -> dict[str, Any] | None:
        for q in self.quotes:
            if q["id"] == quote_id:
                q["state"] = state
                self._log("odoo.state", f"{quote_id} -> {state}", quote_id)
                for job in self.jobs:
                    if job.get("quote_id") == quote_id:
                        if state == "sent":
                            job["status"] = "quote_sent"
                        elif state == "sale":
                            job["status"] = "confirmed"
                        elif state == "cancel":
                            job["status"] = "cancelled"
                return q
        return None

    def evaluation(self) -> dict[str, Any]:
        rows = [j["gold"] for j in self.jobs if j.get("gold")]
        summary = aggregate(rows)
        by_difficulty: dict[str, list] = {}
        for r in rows:
            by_difficulty.setdefault(r["difficulty"], []).append(r)
        summary["by_difficulty"] = {
            k: aggregate(v) for k, v in sorted(by_difficulty.items())
        }
        summary["rows"] = rows
        return summary

    def catalog(self) -> dict[str, Any]:
        return {
            "products": [p.__dict__ for p in PRODUCTS],
            "partners": [p.__dict__ for p in PARTNERS],
        }

    def overview(self) -> dict[str, Any]:
        jobs = self.jobs
        n = len(jobs) or 1
        review = sum(1 for j in jobs if j["status"] == "needs_review")
        auto = sum(1 for j in jobs if j["status"] in ("draft_in_odoo", "quote_sent", "confirmed") and not j.get("reviewed_at"))
        quotes_draft = sum(1 for q in self.quotes if q["state"] == "draft")
        pipeline = round(sum(q["amount_total"] for q in self.quotes if q["state"] in ("draft", "sent")), 2)
        eval_ = self.evaluation()
        return {
            "documents": len(jobs),
            "needs_review": review,
            "auto_share": round(auto / n, 3),
            "quotes": len(self.quotes),
            "quotes_draft": quotes_draft,
            "pipeline_eur": pipeline,
            "sku_recall": eval_.get("sku_recall", 0),
            "cost_per_document_eur": eval_.get("cost_per_document_eur", 0),
            "routing_accuracy": eval_.get("routing_accuracy", 0),
            "llm": llm_settings.public(),
        }


store = Store()
