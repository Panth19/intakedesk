from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .catalog import product_by_sku, partner_by_id


@dataclass
class QuoteLine:
    sku: str
    description: str
    qty: int
    uom: str
    unit_price: float
    discount: float
    tax: float
    subtotal: float
    stock: int
    stock_status: str


@dataclass
class PurchaseSuggestion:
    sku: str
    product: str
    supplier: str
    suggested_qty: int
    reason: str


@dataclass
class OdooQuote:
    id: str
    partner_id: str
    partner_name: str
    state: str
    intent: str
    currency: str
    validity: str
    payment_terms: str
    lines: list[QuoteLine]
    amount_untaxed: float
    amount_tax: float
    amount_total: float
    purchase_suggestions: list[PurchaseSuggestion] = field(default_factory=list)
    notes: str = ""
    created_at: str = ""
    source_document_id: str = ""


TAX = 0.19
VOLUME_DISCOUNT_QTY = 30
VOLUME_DISCOUNT = 0.05


def _next_id(existing: int) -> str:
    return f"S{existing + 10032:05d}"


def stock_status(stock: int, qty: int, reorder: int) -> str:
    if stock >= qty and stock - qty >= reorder:
        return "available"
    if stock >= qty:
        return "available_low"
    if stock > 0:
        return "partial"
    return "out_of_stock"


def build_quote(
    *,
    seq: int,
    partner_id: str,
    intent: str,
    items: list[dict[str, Any]],
    source_document_id: str,
    notes: str = "",
) -> OdooQuote:
    partner = partner_by_id(partner_id)
    partner_name = partner.name if partner else partner_id
    payment = partner.payment_terms if partner else "14 days"
    lines: list[QuoteLine] = []
    suggestions: list[PurchaseSuggestion] = []
    untaxed = 0.0

    for item in items:
        sku = item["sku"]
        qty = int(item["qty"])
        product = product_by_sku(sku)
        if not product:
            continue
        discount = VOLUME_DISCOUNT if qty >= VOLUME_DISCOUNT_QTY else 0.0
        unit = float(item.get("unit_price") or product.list_price)
        subtotal = round(qty * unit * (1 - discount), 2)
        status = stock_status(product.stock, qty, product.reorder_point)
        lines.append(
            QuoteLine(
                sku=sku,
                description=product.name,
                qty=qty,
                uom=product.uom,
                unit_price=unit,
                discount=discount,
                tax=TAX,
                subtotal=subtotal,
                stock=product.stock,
                stock_status=status,
            )
        )
        untaxed += subtotal
        projected = product.stock - qty
        if projected < product.reorder_point:
            sug_qty = max(product.reorder_point * 2 - max(projected, 0), qty)
            suggestions.append(
                PurchaseSuggestion(
                    sku=sku,
                    product=product.name,
                    supplier=product.supplier,
                    suggested_qty=sug_qty,
                    reason=f"Stock {product.stock} vs order {qty}; reorder point {product.reorder_point}",
                )
            )

    tax = round(untaxed * TAX, 2)
    total = round(untaxed + tax, 2)
    now = datetime.utcnow()
    return OdooQuote(
        id=_next_id(seq),
        partner_id=partner_id,
        partner_name=partner_name,
        state="draft",
        intent=intent,
        currency="EUR",
        validity=(now + timedelta(days=14)).strftime("%Y-%m-%d"),
        payment_terms=payment,
        lines=lines,
        amount_untaxed=round(untaxed, 2),
        amount_tax=tax,
        amount_total=total,
        purchase_suggestions=suggestions,
        notes=notes,
        created_at=now.isoformat(timespec="seconds") + "Z",
        source_document_id=source_document_id,
    )


def quote_to_dict(q: OdooQuote) -> dict[str, Any]:
    return {
        "id": q.id,
        "partner_id": q.partner_id,
        "partner_name": q.partner_name,
        "state": q.state,
        "intent": q.intent,
        "currency": q.currency,
        "validity": q.validity,
        "payment_terms": q.payment_terms,
        "lines": [ln.__dict__ for ln in q.lines],
        "amount_untaxed": q.amount_untaxed,
        "amount_tax": q.amount_tax,
        "amount_total": q.amount_total,
        "purchase_suggestions": [s.__dict__ for s in q.purchase_suggestions],
        "notes": q.notes,
        "created_at": q.created_at,
        "source_document_id": q.source_document_id,
    }
