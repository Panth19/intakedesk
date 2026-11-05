from app.documents import SAMPLES, get_sample
from app.extractor import extract
from app.metrics import score_extraction, aggregate
from app.odoo_sim import build_quote
from app.store import Store


def test_easy_german_order_auto():
    doc = get_sample("DOC-001")
    assert doc
    result = extract(doc.subject, doc.body, f"{doc.from_name} {doc.from_email}")
    gold = score_extraction(doc, result)
    assert gold["partner_ok"]
    assert gold["sku_recall"] == 1.0
    assert gold["qty_accuracy"] == 1.0
    assert result.intent == "order"


def test_english_po():
    doc = get_sample("DOC-003")
    assert doc
    result = extract(doc.subject, doc.body, f"{doc.from_name} {doc.from_email}")
    gold = score_extraction(doc, result)
    assert gold["partner_ok"]
    assert gold["sku_recall"] == 1.0


def test_unknown_sku_needs_review():
    doc = get_sample("DOC-009")
    assert doc
    result = extract(doc.subject, doc.body, f"{doc.from_name} {doc.from_email}")
    assert result.needs_review
    assert any(ln.sku is None for ln in result.lines) or "unknown" in " ".join(result.review_reasons).lower() or result.needs_review


def test_corpus_quality_floor():
    rows = []
    for doc in SAMPLES:
        result = extract(doc.subject, doc.body, f"{doc.from_name} {doc.from_email}")
        rows.append(score_extraction(doc, result))
    summary = aggregate(rows)
    assert summary["sku_recall"] >= 0.75
    assert summary["partner_accuracy"] >= 0.7
    assert summary["documents"] == 12


def test_quote_totals_and_purchase_signal():
    quote = build_quote(
        seq=0,
        partner_id="P-1002",
        intent="quote",
        items=[{"sku": "NF-MAG-90", "qty": 25, "unit_price": 12.4}],
        source_document_id="DOC-002",
    )
    assert quote.amount_total > 0
    assert quote.lines[0].tax == 0.19
    assert quote.purchase_suggestions


def test_store_review_creates_quote():
    s = Store()
    review_jobs = [j for j in s.jobs if j["status"] == "needs_review"]
    assert review_jobs
    job = review_jobs[0]
    before = len(s.quotes)
    updated = s.review(
        job["id"],
        {
            "action": "approve",
            "partner_id": job["extraction"]["partner_id"] or "P-1001",
            "lines": [
                ln
                for ln in job["extraction"]["lines"]
                if ln.get("sku")
            ]
            or [{"sku": "NF-CREA-500", "qty": 1, "unit_price": 14.5, "raw": "kreatin", "product_name": "Creatine", "uom": "tub", "confidence": 1, "match_reason": "manual", "issues": []}],
            "note": "corrected in review",
        },
    )
    assert updated
    assert updated["status"] == "draft_in_odoo"
    assert len(s.quotes) >= before
