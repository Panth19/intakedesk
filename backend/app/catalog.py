from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    sku: str
    name: str
    name_de: str
    category: str
    uom: str
    pack_size: str
    list_price: float
    cost: float
    stock: int
    reorder_point: int
    supplier: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class Partner:
    id: str
    name: str
    city: str
    country: str
    lang: str
    email: str
    payment_terms: str
    aliases: list[str] = field(default_factory=list)


PRODUCTS: list[Product] = [
    Product(
        sku="NF-WHEY-VAN-1KG",
        name="Whey Protein Isolate 1kg Vanilla",
        name_de="Molkenprotein Isolat 1kg Vanille",
        category="Protein",
        uom="bag",
        pack_size="1 kg",
        list_price=29.90,
        cost=14.20,
        stock=84,
        reorder_point=40,
        supplier="EuroProtein GmbH",
        aliases=["whey vanilla 1kg", "whey vanille", "molke vanille 1kg", "protein vanille 1kg", "whey 1kg vanille"],
    ),
    Product(
        sku="NF-WHEY-VAN-5KG",
        name="Whey Protein Isolate 5kg Vanilla",
        name_de="Molkenprotein Isolat 5kg Vanille",
        category="Protein",
        uom="bag",
        pack_size="5 kg",
        list_price=119.00,
        cost=58.00,
        stock=22,
        reorder_point=12,
        supplier="EuroProtein GmbH",
        aliases=["whey 5kg", "whey vanille 5kg", "molke 5kg", "protein 5kg vanille"],
    ),
    Product(
        sku="NF-WHEY-CHOC-1KG",
        name="Whey Protein Isolate 1kg Chocolate",
        name_de="Molkenprotein Isolat 1kg Schokolade",
        category="Protein",
        uom="bag",
        pack_size="1 kg",
        list_price=29.90,
        cost=14.20,
        stock=61,
        reorder_point=40,
        supplier="EuroProtein GmbH",
        aliases=["whey schoko", "whey chocolate", "molke schokolade", "protein schoko 1kg"],
    ),
    Product(
        sku="NF-CREA-500",
        name="Creatine Monohydrate 500g",
        name_de="Kreatin Monohydrat 500g",
        category="Performance",
        uom="tub",
        pack_size="500 g",
        list_price=14.50,
        cost=5.80,
        stock=140,
        reorder_point=50,
        supplier="RheinActives AG",
        aliases=["creatine", "kreatin", "creatin monohydrat", "creatine 500"],
    ),
    Product(
        sku="NF-OMEGA-90",
        name="Omega-3 Softgels 90",
        name_de="Omega-3 Weichkapseln 90",
        category="Essentials",
        uom="bottle",
        pack_size="90 caps",
        list_price=18.90,
        cost=7.40,
        stock=36,
        reorder_point=40,
        supplier="NordicMarine AS",
        aliases=["omega 3", "omega-3", "fischol", "fischöl", "omega3"],
    ),
    Product(
        sku="NF-VITD-120",
        name="Vitamin D3 2000 IU 120 tablets",
        name_de="Vitamin D3 2000 I.E. 120 Tabletten",
        category="Essentials",
        uom="bottle",
        pack_size="120 tabs",
        list_price=9.90,
        cost=3.10,
        stock=210,
        reorder_point=80,
        supplier="RheinActives AG",
        aliases=["vitamin d", "vitamin d3", "d3 2000", "vit d"],
    ),
    Product(
        sku="NF-MAG-90",
        name="Magnesium Citrate 90",
        name_de="Magnesiumcitrat 90",
        category="Essentials",
        uom="bottle",
        pack_size="90 caps",
        list_price=12.40,
        cost=4.20,
        stock=18,
        reorder_point=30,
        supplier="RheinActives AG",
        aliases=["magnesium", "magnesiumcitrat", "mag citrat"],
    ),
    Product(
        sku="NF-COLL-300",
        name="Collagen Peptides 300g",
        name_de="Kollagenpeptide 300g",
        category="Recovery",
        uom="tub",
        pack_size="300 g",
        list_price=22.00,
        cost=9.60,
        stock=47,
        reorder_point=20,
        supplier="Bavaria Collagen KG",
        aliases=["collagen", "kollagen", "kollagenpeptide", "collagen peptides"],
    ),
    Product(
        sku="NF-BCAA-400",
        name="BCAA 2:1:1 400g",
        name_de="BCAA 2:1:1 400g",
        category="Performance",
        uom="tub",
        pack_size="400 g",
        list_price=19.90,
        cost=8.10,
        stock=55,
        reorder_point=25,
        supplier="EuroProtein GmbH",
        aliases=["bcaa", "bcaa 2:1:1", "branched chain"],
    ),
    Product(
        sku="NF-PRE-300",
        name="Pre-Workout Citrus 300g",
        name_de="Pre-Workout Zitrus 300g",
        category="Performance",
        uom="tub",
        pack_size="300 g",
        list_price=24.90,
        cost=10.40,
        stock=9,
        reorder_point=20,
        supplier="EuroProtein GmbH",
        aliases=["pre workout", "pre-workout", "preworkout", "booster", "pre workout zitrus", "zitrus booster"],
    ),
    Product(
        sku="NF-VEGAN-1KG",
        name="Pea Protein 1kg Unflavoured",
        name_de="Erbsenprotein 1kg Neutral",
        category="Protein",
        uom="bag",
        pack_size="1 kg",
        list_price=26.50,
        cost=12.80,
        stock=33,
        reorder_point=15,
        supplier="PlantFuel NL",
        aliases=["pea protein", "erbsenprotein", "vegan protein", "pflanzliches protein"],
    ),
    Product(
        sku="NF-BAR-BOX24",
        name="Protein Bar Mix Box 24",
        name_de="Proteinriegel Mix Karton 24",
        category="Impulse",
        uom="carton",
        pack_size="24 bars",
        list_price=31.20,
        cost=16.80,
        stock=72,
        reorder_point=24,
        supplier="SnackLine GmbH",
        aliases=["proteinriegel", "protein bars", "riegel karton", "riegel box", "bar mix"],
    ),
]

PARTNERS: list[Partner] = [
    Partner(
        id="P-1001",
        name="Fitness First Frankfurt GmbH",
        city="Frankfurt am Main",
        country="DE",
        lang="de",
        email="einkauf@fitnessfirst-ffm.de",
        payment_terms="14 days",
        aliases=["fitness first", "fitness first frankfurt", "ff frankfurt"],
    ),
    Partner(
        id="P-1002",
        name="Apotheke am Markt Griesheim",
        city="Griesheim",
        country="DE",
        lang="de",
        email="bestellung@apotheke-markt-griesheim.de",
        payment_terms="30 days",
        aliases=["apotheke am markt", "apotheke griesheim", "markt apotheke"],
    ),
    Partner(
        id="P-1003",
        name="BioMarkt Darmstadt",
        city="Darmstadt",
        country="DE",
        lang="de",
        email="order@biomarkt-darmstadt.de",
        payment_terms="14 days",
        aliases=["biomarkt darmstadt", "bio markt darmstadt"],
    ),
    Partner(
        id="P-1004",
        name="Gym24 Mainz",
        city="Mainz",
        country="DE",
        lang="de",
        email="shop@gym24-mainz.de",
        payment_terms="7 days",
        aliases=["gym24", "gym 24 mainz", "gym24 mainz"],
    ),
    Partner(
        id="P-1005",
        name="Supplement Store Cologne",
        city="Cologne",
        country="DE",
        lang="en",
        email="purchasing@suppstore.cologne",
        payment_terms="14 days",
        aliases=["supplement store", "suppstore cologne", "supplement store cologne"],
    ),
    Partner(
        id="P-1006",
        name="Sportnahrung Berlin UG",
        city="Berlin",
        country="DE",
        lang="de",
        email="einkauf@sportnahrung.berlin",
        payment_terms="21 days",
        aliases=["sportnahrung berlin", "sportnahrung"],
    ),
    Partner(
        id="P-1007",
        name="PharmaPlus Wiesbaden",
        city="Wiesbaden",
        country="DE",
        lang="de",
        email="order@pharmaplus-wi.de",
        payment_terms="30 days",
        aliases=["pharmaplus", "pharma plus wiesbaden"],
    ),
    Partner(
        id="P-1008",
        name="CrossFit Rhine",
        city="Rüsselsheim",
        country="DE",
        lang="en",
        email="coach@crossfit-rhine.de",
        payment_terms="7 days",
        aliases=["crossfit rhine", "cf rhine", "crossfit rhein"],
    ),
    Partner(
        id="P-1009",
        name="NutriRetail Amsterdam BV",
        city="Amsterdam",
        country="NL",
        lang="en",
        email="buy@nutriretail.nl",
        payment_terms="21 days",
        aliases=["nutriretail", "nutri retail amsterdam"],
    ),
    Partner(
        id="P-1010",
        name="Campus Fit Hochschule RheinMain",
        city="Wiesbaden",
        country="DE",
        lang="de",
        email="campusfit@hs-rm.de",
        payment_terms="14 days",
        aliases=["campus fit", "hochschule rheinmain", "hs-rm campus"],
    ),
]


def product_by_sku(sku: str) -> Product | None:
    sku_u = sku.upper()
    for p in PRODUCTS:
        if p.sku == sku_u:
            return p
    return None


def partner_by_id(pid: str) -> Partner | None:
    for p in PARTNERS:
        if p.id == pid:
            return p
    return None
