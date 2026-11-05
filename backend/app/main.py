from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.responses import FileResponse

from .settings import llm_settings
from .store import store


app = FastAPI(
    title="IntakeDesk – Nutrifill Order & Quote Intake",
    description="AI intake for nutritional wholesale: extract orders from DE/EN emails, draft Odoo quotes, route uncertain cases to review.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    source: str = "email"
    from_name: str = ""
    from_email: str = ""
    subject: str
    body: str
    sample_id: str | None = None
    language: str | None = None
    use_llm: bool = True


class ReviewLine(BaseModel):
    raw: str = ""
    sku: str | None = None
    product_name: str | None = None
    qty: int = 1
    uom: str | None = None
    unit_price: float | None = None
    confidence: float = 1.0
    match_reason: str = "manual"
    issues: list[str] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    action: str = "approve"
    partner_id: str | None = None
    intent: str | None = None
    lines: list[ReviewLine] | None = None
    note: str = ""


class QuoteStateRequest(BaseModel):
    state: str


class WebhookIngest(BaseModel):
    from_name: str = ""
    from_email: str = ""
    subject: str = ""
    body: str = ""
    source: str = "n8n"
    use_llm: bool = True


class LlmConfigRequest(BaseModel):
    enabled: bool = True
    provider: str = "groq"
    api_key: str = ""
    base_url: str = ""
    model: str = ""


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "intakedesk",
        "llm_mode": llm_settings.public()["mode"],
    }


@app.get("/api/settings/llm")
def get_llm_settings() -> dict[str, Any]:
    return llm_settings.public()


@app.post("/api/settings/llm")
def set_llm_settings(req: LlmConfigRequest) -> dict[str, Any]:
    llm_settings.update(req.model_dump())
    store._log(
        "llm.config",
        f"{llm_settings.provider} {llm_settings.model} enabled={llm_settings.enabled}",
        "llm",
    )
    return llm_settings.public()


@app.post("/api/settings/llm/test")
def test_llm() -> dict[str, Any]:
    from .llm import extract_document

    if not llm_settings.api_key:
        raise HTTPException(400, "No API key configured")
    sample_body = (
        "Hallo Nutrifill, bitte 2 x Molkenprotein Isolat 1kg Vanille "
        "für Fitness First Frankfurt. Danke"
    )
    try:
        result = extract_document(
            "Test Nachbestellung",
            sample_body,
            "Lisa Berger einkauf@fitnessfirst-ffm.de",
            prefer_llm=True,
        )
    except Exception as exc:
        raise HTTPException(502, str(exc)[:400]) from exc
    return {
        "ok": True,
        "mode": "llm" if result.notes.startswith("llm:") else "fallback",
        "partner_name": result.partner_name,
        "intent": result.intent,
        "lines": [
            {"sku": ln.sku, "qty": ln.qty, "raw": ln.raw, "confidence": ln.confidence}
            for ln in result.lines
        ],
        "notes": result.notes,
        "cost_eur": result.estimated_cost_eur,
    }


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    return store.overview()


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return store.catalog()


@app.get("/api/jobs")
def list_jobs(status: str | None = None) -> list[dict[str, Any]]:
    jobs = store.jobs
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    return jobs


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@app.post("/api/ingest")
def ingest(req: IngestRequest) -> dict[str, Any]:
    return store.ingest(req.model_dump())


@app.post("/api/webhook/n8n")
def n8n_webhook(req: WebhookIngest) -> dict[str, Any]:
    return store.ingest(req.model_dump())


@app.post("/api/jobs/{job_id}/review")
def review_job(job_id: str, req: ReviewRequest) -> dict[str, Any]:
    payload = req.model_dump()
    if payload.get("lines") is not None:
        payload["lines"] = [ln if isinstance(ln, dict) else ln for ln in payload["lines"]]
    job = store.review(job_id, payload)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@app.get("/api/quotes")
def list_quotes() -> list[dict[str, Any]]:
    return store.quotes


@app.get("/api/quotes/{quote_id}")
def get_quote(quote_id: str) -> dict[str, Any]:
    for q in store.quotes:
        if q["id"] == quote_id:
            return q
    raise HTTPException(404, "quote not found")


@app.post("/api/quotes/{quote_id}/state")
def quote_state(quote_id: str, req: QuoteStateRequest) -> dict[str, Any]:
    allowed = {"draft", "sent", "sale", "cancel"}
    if req.state not in allowed:
        raise HTTPException(400, f"state must be one of {sorted(allowed)}")
    q = store.set_quote_state(quote_id, req.state)
    if not q:
        raise HTTPException(404, "quote not found")
    return q


@app.get("/api/evaluation")
def evaluation() -> dict[str, Any]:
    return store.evaluation()


@app.get("/api/audit")
def audit() -> list[dict[str, Any]]:
    return store.audit[:80]


@app.get("/api/samples")
def samples() -> list[dict[str, Any]]:
    from .documents import SAMPLES

    return [
        {
            "id": s.id,
            "source": s.source,
            "language": s.language,
            "intent": s.intent,
            "from_name": s.from_name,
            "from_email": s.from_email,
            "subject": s.subject,
            "body": s.body,
            "gold_partner_id": s.gold_partner_id,
            "gold_lines": [g.__dict__ for g in s.gold_lines],
            "expected_auto": s.expected_auto,
            "difficulty": s.difficulty,
            "tags": s.tags,
        }
        for s in SAMPLES
    ]


@app.get("/api/workflow")
def workflow() -> dict[str, Any]:
    return {
        "title": "IntakeDesk workflow",
        "steps": [
            {
                "id": "mail",
                "title": "Mailbox / PDF drop",
                "tool": "n8n IMAP + PDF parse",
                "detail": "German and English customer emails and order PDFs land in einkauf@nutrifill.example",
            },
            {
                "id": "extract",
                "title": "LLM extraction",
                "tool": "Groq / OpenAI-compatible chat API",
                "detail": "Customer, intent, line items, delivery date, confidence. Falls back to catalog rules if the key is missing.",
            },
            {
                "id": "route",
                "title": "Confidence router",
                "tool": "threshold 0.82",
                "detail": "High confidence drafts an Odoo quotation. Low confidence goes to human review.",
            },
            {
                "id": "odoo",
                "title": "Odoo draft quote",
                "tool": "Odoo sale.order (simulated)",
                "detail": "Partner match, tax 19%, volume discount, stock check, purchase suggestion.",
            },
            {
                "id": "purchase",
                "title": "Purchasing signal",
                "tool": "Odoo purchase.order suggestion",
                "detail": "If stock falls below reorder point, a supplier RFQ suggestion is created.",
            },
            {
                "id": "review",
                "title": "Human review queue",
                "tool": "IntakeDesk UI",
                "detail": "Working student corrects SKU, qty, customer; one click posts the draft to Odoo.",
            },
            {
                "id": "eval",
                "title": "Weekly evaluation",
                "tool": "/api/evaluation",
                "detail": "SKU recall/precision, auto-handle share, routing accuracy, EUR cost per document.",
            },
        ],
        "kpis": [
            "extraction accuracy (SKU + qty)",
            "share handled without review",
            "cost per document",
            "routing accuracy vs gold labels",
        ],
        "stack": ["n8n", "FastAPI", "Odoo Community", "React", "Groq LLM", "synthetic DE/EN corpus"],
    }


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(404, "not found")
        file = DIST / full_path
        if full_path and file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(DIST / "index.html")
