from app.llm import _hydrate_llm, extract_document
from app.settings import llm_settings


def test_rules_used_when_llm_disabled():
    llm_settings.enabled = False
    llm_settings.api_key = ""
    result = extract_document(
        "Nachbestellung Protein – Studio Ostend",
        "24 x Molkenprotein Isolat 1kg Vanille\n12 x Molkenprotein Isolat 1kg Schokolade\n10 Stk Kreatin Monohydrat 500g\nLisa Berger\neinkauf@fitnessfirst-ffm.de",
        "Lisa Berger einkauf@fitnessfirst-ffm.de",
        prefer_llm=True,
    )
    assert result.notes.startswith("rules")
    assert any(ln.sku == "NF-WHEY-VAN-1KG" for ln in result.lines)


def test_hydrate_llm_json():
    parsed = {
        "partner_id": "P-1001",
        "intent": "order",
        "language": "de",
        "requested_delivery": "18.11.2026",
        "notes": "studio ostend",
        "lines": [
            {"raw": "24 x whey vanille 1kg", "sku": "NF-WHEY-VAN-1KG", "qty": 24, "confidence": 0.95},
            {"raw": "unknown tropical shake", "sku": None, "qty": 5, "confidence": 0.2},
        ],
    }
    result = _hydrate_llm(parsed, "Bestellung", "body", "Lisa einkauf@fitnessfirst-ffm.de", 0.001)
    assert result.partner_id == "P-1001"
    assert result.intent == "order"
    assert result.needs_review
    assert result.lines[0].sku == "NF-WHEY-VAN-1KG"
    assert result.lines[0].qty == 24
    assert any(ln.sku is None for ln in result.lines)


def test_settings_mask_and_enable(monkeypatch):
    llm_settings.api_key = ""
    llm_settings.enabled = False
    llm_settings.update(
        {
            "enabled": True,
            "provider": "groq",
            "api_key": "gsk_testkey_12345678",
            "base_url": "",
            "model": "",
        }
    )
    pub = llm_settings.public()
    assert pub["enabled"] is True
    assert pub["configured"] is True
    assert "gsk_" in pub["api_key_masked"]
    assert "••••" in pub["api_key_masked"]
    assert pub["model"] == "llama-3.1-8b-instant"
    llm_settings.api_key = ""
    llm_settings.enabled = False
