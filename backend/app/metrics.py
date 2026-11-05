from __future__ import annotations

from typing import Any

from .documents import SampleDocument, GoldLine
from .extractor import ExtractionResult


def line_key(sku: str, qty: int) -> tuple[str, int]:
    return (sku, qty)


def score_extraction(gold: SampleDocument, result: ExtractionResult) -> dict[str, Any]:
    gold_set = {line_key(g.sku, g.qty) for g in gold.gold_lines}
    pred_set = {line_key(ln.sku, ln.qty) for ln in result.lines if ln.sku}
    pred_skus = {ln.sku for ln in result.lines if ln.sku}
    gold_skus = {g.sku for g in gold.gold_lines}

    sku_tp = len(pred_skus & gold_skus)
    sku_fp = len(pred_skus - gold_skus)
    sku_fn = len(gold_skus - pred_skus)
    line_tp = len(pred_set & gold_set)

    partner_ok = result.partner_id == gold.gold_partner_id
    intent_ok = result.intent == gold.intent
    sku_recall = sku_tp / len(gold_skus) if gold_skus else 1.0
    sku_precision = sku_tp / len(pred_skus) if pred_skus else 0.0
    qty_acc = line_tp / len(gold_set) if gold_set else 0.0

    auto_correct = (
        (not result.needs_review)
        and partner_ok
        and sku_recall == 1.0
        and sku_precision == 1.0
        and qty_acc == 1.0
    )
    routing_ok = result.needs_review == (not gold.expected_auto)

    return {
        "document_id": gold.id,
        "partner_ok": partner_ok,
        "intent_ok": intent_ok,
        "sku_recall": round(sku_recall, 3),
        "sku_precision": round(sku_precision, 3),
        "qty_accuracy": round(qty_acc, 3),
        "sku_tp": sku_tp,
        "sku_fp": sku_fp,
        "sku_fn": sku_fn,
        "auto_handled": not result.needs_review,
        "expected_auto": gold.expected_auto,
        "routing_ok": routing_ok,
        "auto_correct": auto_correct,
        "cost_eur": result.estimated_cost_eur,
        "confidence": result.overall_confidence,
        "difficulty": gold.difficulty,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows) or 1
    def avg(key: str) -> float:
        return round(sum(r[key] for r in rows) / n, 3)

    return {
        "documents": len(rows),
        "partner_accuracy": avg("partner_ok") if rows else 0,
        "intent_accuracy": avg("intent_ok") if rows else 0,
        "sku_recall": avg("sku_recall") if rows else 0,
        "sku_precision": avg("sku_precision") if rows else 0,
        "qty_accuracy": avg("qty_accuracy") if rows else 0,
        "share_auto": round(sum(1 for r in rows if r["auto_handled"]) / n, 3),
        "share_auto_correct": round(sum(1 for r in rows if r["auto_correct"]) / n, 3),
        "routing_accuracy": avg("routing_ok") if rows else 0,
        "cost_per_document_eur": round(sum(r["cost_eur"] for r in rows) / n, 4) if rows else 0,
        "total_cost_eur": round(sum(r["cost_eur"] for r in rows), 4) if rows else 0,
    }
