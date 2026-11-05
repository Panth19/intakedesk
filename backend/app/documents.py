from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GoldLine:
    sku: str
    qty: int


@dataclass
class SampleDocument:
    id: str
    source: str
    language: str
    intent: str
    from_name: str
    from_email: str
    subject: str
    body: str
    gold_partner_id: str
    gold_lines: list[GoldLine]
    expected_auto: bool
    difficulty: str
    tags: list[str] = field(default_factory=list)


SAMPLES: list[SampleDocument] = [
    SampleDocument(
        id="DOC-001",
        source="email",
        language="de",
        intent="order",
        from_name="Lisa Berger",
        from_email="einkauf@fitnessfirst-ffm.de",
        subject="Nachbestellung Protein – Studio Ostend",
        body=(
            "Hallo Nutrifill Team,\n\n"
            "bitte folgende Nachbestellung für Fitness First Frankfurt aufnehmen:\n"
            "- 24 x Molkenprotein Isolat 1kg Vanille\n"
            "- 12 x Molkenprotein Isolat 1kg Schokolade\n"
            "- 10 Stk Kreatin Monohydrat 500g\n\n"
            "Lieferung bis 18.11.2026 an unser Lager in Frankfurt-Ostend.\n"
            "Vielen Dank\nLisa Berger\nEinkauf"
        ),
        gold_partner_id="P-1001",
        gold_lines=[
            GoldLine("NF-WHEY-VAN-1KG", 24),
            GoldLine("NF-WHEY-CHOC-1KG", 12),
            GoldLine("NF-CREA-500", 10),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["reorder", "gym"],
    ),
    SampleDocument(
        id="DOC-002",
        source="email",
        language="de",
        intent="quote",
        from_name="Apotheke am Markt",
        from_email="bestellung@apotheke-markt-griesheim.de",
        subject="Anfrage Angebot Omega-3 und Vitamin D",
        body=(
            "Guten Tag,\n"
            "wir benötigen ein Angebot für:\n"
            "Omega-3 Weichkapseln 90 – 40 Flaschen\n"
            "Vitamin D3 2000 I.E. 120 Tabletten – 60 Flaschen\n"
            "Magnesiumcitrat 90 – 25 Flaschen\n\n"
            "Bitte netto, Lieferung nach Griesheim, Zahlungsziel 30 Tage.\n"
            "Mit freundlichen Grüßen\nApotheke am Markt Griesheim"
        ),
        gold_partner_id="P-1002",
        gold_lines=[
            GoldLine("NF-OMEGA-90", 40),
            GoldLine("NF-VITD-120", 60),
            GoldLine("NF-MAG-90", 25),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["pharmacy", "rfq"],
    ),
    SampleDocument(
        id="DOC-003",
        source="email",
        language="en",
        intent="order",
        from_name="Purchasing",
        from_email="purchasing@suppstore.cologne",
        subject="PO – weekly restock",
        body=(
            "Hi Nutrifill,\n"
            "Please process this purchase order for Supplement Store Cologne:\n"
            "8 bags Whey Protein Isolate 5kg Vanilla\n"
            "20 bottles Omega-3 Softgels 90\n"
            "6 cartons Protein Bar Mix Box 24\n"
            "Need delivery this week.\n"
            "Thanks"
        ),
        gold_partner_id="P-1005",
        gold_lines=[
            GoldLine("NF-WHEY-VAN-5KG", 8),
            GoldLine("NF-OMEGA-90", 20),
            GoldLine("NF-BAR-BOX24", 6),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["english", "po"],
    ),
    SampleDocument(
        id="DOC-004",
        source="pdf",
        language="de",
        intent="order",
        from_name="BioMarkt Darmstadt",
        from_email="order@biomarkt-darmstadt.de",
        subject="Bestellformular KW46 (PDF-Text)",
        body=(
            "BIOMARKT DARMSTADT – BESTELLFORMULAR\n"
            "Kunde: BioMarkt Darmstadt\n"
            "Position 1: Erbsenprotein 1kg Neutral     Menge 15\n"
            "Position 2: Kollagenpeptide 300g           Menge 20\n"
            "Position 3: Vitamin D3 2000 I.E. 120       Menge 30\n"
            "Liefertermin: nächste Woche\n"
            "Unterschrift: Filialleitung"
        ),
        gold_partner_id="P-1003",
        gold_lines=[
            GoldLine("NF-VEGAN-1KG", 15),
            GoldLine("NF-COLL-300", 20),
            GoldLine("NF-VITD-120", 30),
        ],
        expected_auto=True,
        difficulty="medium",
        tags=["pdf", "form"],
    ),
    SampleDocument(
        id="DOC-005",
        source="email",
        language="de",
        intent="quote",
        from_name="Jonas",
        from_email="shop@gym24-mainz.de",
        subject="Brauchen mal schnell Preise",
        body=(
            "Hey,\n"
            "könnt ihr uns mal ein Angebot schicken für Gym24?\n"
            "Wir brauchen so 15 whey vanille 1kg und 8 pre workout zitrus "
            "und irgendwie noch kreatin, sagen wir 12 dosen.\n"
            "Ist das express möglich?\n"
            "Jonas"
        ),
        gold_partner_id="P-1004",
        gold_lines=[
            GoldLine("NF-WHEY-VAN-1KG", 15),
            GoldLine("NF-PRE-300", 8),
            GoldLine("NF-CREA-500", 12),
        ],
        expected_auto=False,
        difficulty="hard",
        tags=["informal", "ambiguous-uom"],
    ),
    SampleDocument(
        id="DOC-006",
        source="email",
        language="de",
        intent="order",
        from_name="Einkauf",
        from_email="einkauf@sportnahrung.berlin",
        subject="Nachbestellung BCAA / Riegel / Whey",
        body=(
            "Sportnahrung Berlin UG\n"
            "Bitte liefern:\n"
            "40 x BCAA 2:1:1 400g\n"
            "18 x Proteinriegel Mix Karton 24\n"
            "6 x Molkenprotein Isolat 5kg Vanille\n"
            "Bitte auf unser Berliner Lager, Zahlungsziel 21 Tage."
        ),
        gold_partner_id="P-1006",
        gold_lines=[
            GoldLine("NF-BCAA-400", 40),
            GoldLine("NF-BAR-BOX24", 18),
            GoldLine("NF-WHEY-VAN-5KG", 6),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["b2b"],
    ),
    SampleDocument(
        id="DOC-007",
        source="email",
        language="de",
        intent="quote",
        from_name="M. Krüger",
        from_email="order@pharmaplus-wi.de",
        subject="Angebot Apotheken-Sortiment Q4",
        body=(
            "PharmaPlus Wiesbaden bittet um Angebot:\n"
            "Magnesiumcitrat 90 : 80\n"
            "Omega-3 90 Kapseln : 50\n"
            "Vitamin D3 2000 : 100\n"
            "Kollagenpeptide 300g : 12\n"
            "Bitte Staffelpreis falls möglich."
        ),
        gold_partner_id="P-1007",
        gold_lines=[
            GoldLine("NF-MAG-90", 80),
            GoldLine("NF-OMEGA-90", 50),
            GoldLine("NF-VITD-120", 100),
            GoldLine("NF-COLL-300", 12),
        ],
        expected_auto=False,
        difficulty="medium",
        tags=["volume", "stock-risk"],
    ),
    SampleDocument(
        id="DOC-008",
        source="email",
        language="en",
        intent="order",
        from_name="Coach Alex",
        from_email="coach@crossfit-rhine.de",
        subject="Box restock – CrossFit Rhine",
        body=(
            "Hey team,\n"
            "Need for CrossFit Rhine:\n"
            "10x creatine 500\n"
            "8x pre-workout citrus 300g\n"
            "12x whey chocolate 1kg\n"
            "4x protein bar mix box\n"
            "ASAP please – competition weekend.\n"
            "Alex"
        ),
        gold_partner_id="P-1008",
        gold_lines=[
            GoldLine("NF-CREA-500", 10),
            GoldLine("NF-PRE-300", 8),
            GoldLine("NF-WHEY-CHOC-1KG", 12),
            GoldLine("NF-BAR-BOX24", 4),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["english", "urgent"],
    ),
    SampleDocument(
        id="DOC-009",
        source="pdf",
        language="en",
        intent="quote",
        from_name="Buyer NL",
        from_email="buy@nutriretail.nl",
        subject="RFQ NutriRetail Amsterdam – private label trial",
        body=(
            "RFQ / QUOTATION REQUEST\n"
            "Company: NutriRetail Amsterdam BV\n"
            "Please quote CIP Amsterdam:\n"
            "Item A: Pea Protein 1kg unflavoured     Qty 40\n"
            "Item B: Whey Isolate 5kg Vanilla        Qty 10\n"
            "Item C: Collagen Peptides 300g          Qty 25\n"
            "Also include 5 units of 'recovery shake tropical' if you have it.\n"
            "Need prices this week."
        ),
        gold_partner_id="P-1009",
        gold_lines=[
            GoldLine("NF-VEGAN-1KG", 40),
            GoldLine("NF-WHEY-VAN-5KG", 10),
            GoldLine("NF-COLL-300", 25),
        ],
        expected_auto=False,
        difficulty="hard",
        tags=["unknown-sku", "export"],
    ),
    SampleDocument(
        id="DOC-010",
        source="email",
        language="de",
        intent="order",
        from_name="Campus Fit",
        from_email="campusfit@hs-rm.de",
        subject="Semester-Start Bestellung Campus Fit",
        body=(
            "Hallo,\n"
            "Campus Fit Hochschule RheinMain bestellt für die Theke:\n"
            "20 Proteinriegel Mix Karton 24\n"
            "10 Molkenprotein Isolat 1kg Vanille\n"
            "10 Molkenprotein Isolat 1kg Schokolade\n"
            "8 BCAA 2:1:1 400g\n"
            "Lieferung KW 47 bitte.\n"
            "Danke!"
        ),
        gold_partner_id="P-1010",
        gold_lines=[
            GoldLine("NF-BAR-BOX24", 20),
            GoldLine("NF-WHEY-VAN-1KG", 10),
            GoldLine("NF-WHEY-CHOC-1KG", 10),
            GoldLine("NF-BCAA-400", 8),
        ],
        expected_auto=True,
        difficulty="easy",
        tags=["campus"],
    ),
    SampleDocument(
        id="DOC-011",
        source="email",
        language="de",
        intent="order",
        from_name="Unbekannt",
        from_email="info@studio-west.de",
        subject="Bestellung whey und so",
        body=(
            "Hallo,\n"
            "wir sind ein neues Studio in Frankfurt und wollen mal testen.\n"
            "Schickt uns 5 whey 1kg (egal welche sorte) und 3 booster.\n"
            "Rechnung an Studio West.\n"
            "Danke"
        ),
        gold_partner_id="P-1001",
        gold_lines=[
            GoldLine("NF-WHEY-VAN-1KG", 5),
            GoldLine("NF-PRE-300", 3),
        ],
        expected_auto=False,
        difficulty="hard",
        tags=["unknown-customer", "ambiguous"],
    ),
    SampleDocument(
        id="DOC-012",
        source="email",
        language="en",
        intent="quote",
        from_name="Purchasing",
        from_email="purchasing@suppstore.cologne",
        subject="Can you quote creatine + magnesium?",
        body=(
            "Supplement Store Cologne here.\n"
            "Quote please:\n"
            "Creatine Monohydrate 500g x 50\n"
            "Magnesium Citrate 90 x 40\n"
            "Vitamin D3 2000 IU 120 tablets x 40\n"
            "If magnesium is short, propose a substitute."
        ),
        gold_partner_id="P-1005",
        gold_lines=[
            GoldLine("NF-CREA-500", 50),
            GoldLine("NF-MAG-90", 40),
            GoldLine("NF-VITD-120", 40),
        ],
        expected_auto=False,
        difficulty="medium",
        tags=["substitution", "stock-risk"],
    ),
]


def get_sample(doc_id: str) -> SampleDocument | None:
    for d in SAMPLES:
        if d.id == doc_id:
            return d
    return None
