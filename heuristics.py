"""Deterministic scam / counterfeit signals for a shopping listing.

No AI and no network here, so results are fast, free and repeatable.
The ideas come from brand-circumvention work in IPR moderation:
  - brand names disguised with spaces, dots, leetspeak or hidden characters
  - counterfeit wording ("1:1", "OEM", "AAA", "copy ori" ...)
  - product-line names used with no brand name
  - price far below the official price
"""
import re
import unicodedata

BRANDS = [
    "nike", "adidas", "puma", "apple", "samsung", "sony", "xiaomi", "huawei",
    "gucci", "prada", "chanel", "dior", "rolex", "casio", "lego", "dyson",
    "canon", "nikon", "fila", "reebok", "converse", "vans", "levis",
    "hermes", "balenciaga", "lacoste", "oakley", "rayban", "jbl", "bose",
    "logitech", "razer", "asus", "lenovo", "oppo", "vivo", "realme",
    "louisvuitton", "uniqlo", "zara", "skechers", "newbalance", "underarmour",
]

# product line -> brand (a product line alone is NOT a valid brand mark)
PRODUCT_LINES = {
    "air jordan": "nike", "air max": "nike", "airforce": "nike",
    "yeezy": "adidas", "ultraboost": "adidas", "superstar": "adidas",
    "iphone": "apple", "airpods": "apple", "macbook": "apple", "ipad": "apple",
    "galaxy": "samsung", "playstation": "sony", "walkman": "sony",
    "g-shock": "casio", "gshock": "casio", "airwrap": "dyson",
}

COUNTERFEIT_TERMS = [
    r"1\s*:\s*1", r"\boem\b", r"\baaa\+*\b", r"\bgrade\s*a\b", r"\bmirror\s*quality\b",
    r"\breplica\b", r"\binspired\b", r"\bhigh\s*copy\b", r"\bcopy\s*ori\b",
    r"\bsuper\s*copy\b", r"\bkw\s*super\b", r"\bunbranded\b", r"\bno\s*logo\b",
    r"\btiruan\b", r"\bcopy\s*original\b", r"\bori\s*quality\b", r"\bmaster\s*copy\b",
    r"\bfactory\s*direct\s*brand\b", r"\bsame\s*as\s*original\b",
]

_LEET = {
    "a": "[a4@]", "e": "[e3]", "i": "[i1!|l]", "o": "[o0]",
    "s": "[s5$]", "t": "[t7]", "l": "[l1|]",
}
_SEP = r"[\s\.\-_*·•]{0,2}"
_ZERO_WIDTH = re.compile("[\u200b-\u200f\u2060\ufeff]")
_NON_LATIN_LOOKALIKE = re.compile("[\u0370-\u03ff\u0400-\u04ff]")  # Greek / Cyrillic


def _brand_pattern(brand: str) -> re.Pattern:
    parts = [_LEET.get(ch, re.escape(ch)) for ch in brand]
    body = _SEP.join(parts)
    return re.compile(rf"(?<![a-z0-9])({body})(?![a-z0-9])", re.IGNORECASE)


_BRAND_PATTERNS = {b: _brand_pattern(b) for b in BRANDS}
_COUNTERFEIT_RE = [re.compile(t, re.IGNORECASE) for t in COUNTERFEIT_TERMS]


def find_disguised_brands(text: str) -> list[str]:
    """Brands written in a disguised way (not plain). Returns brand names."""
    found = []
    for brand, pat in _BRAND_PATTERNS.items():
        for m in pat.finditer(text):
            if m.group(1).lower() != brand:  # not the plain spelling
                found.append(brand)
                break
    return found


def find_plain_brands(text: str) -> set[str]:
    low = text.lower()
    return {b for b in BRANDS if re.search(rf"(?<![a-z0-9]){b}(?![a-z0-9])", low)}


def analyze_listing(title: str, listed_price: float | None = None,
                    official_price: float | None = None) -> dict:
    """Return {score, verdict, reasons, price_ratio}. Score 0-100 (higher = riskier)."""
    reasons: list[str] = []
    score = 0

    disguised = find_disguised_brands(title)
    if disguised:
        score += 35
        reasons.append(f"the {disguised[0]} brand name is written in a disguised way")

    if _ZERO_WIDTH.search(title):
        score += 25
        reasons.append("the title has hidden characters")
    if _NON_LATIN_LOOKALIKE.search(title) and re.search(r"[A-Za-z]", title):
        score += 20
        reasons.append("the title mixes look-alike letters from other alphabets")

    hits = [p.pattern for p in _COUNTERFEIT_RE if p.search(title)]
    if hits:
        score += min(30 + 5 * (len(hits) - 1), 40)
        reasons.append("the wording looks like counterfeit sales language")

    low = title.lower()
    plain = find_plain_brands(title)
    for line, brand in PRODUCT_LINES.items():
        if line in low and brand not in plain and not disguised:
            score += 10
            reasons.append(f"it says {line} but never names the {brand} brand")
            break

    ratio = None
    if listed_price is not None and official_price:
        ratio = listed_price / official_price
        pct = round(ratio * 100)
        if ratio < 0.3:
            score += 45
            reasons.append(f"the price is only {pct} percent of the official price")
        elif ratio < 0.5:
            score += 30
            reasons.append(f"the price is only {pct} percent of the official price")
        elif ratio < 0.7:
            score += 15
            reasons.append(f"the price is {pct} percent of the official price")

    score = min(score, 100)
    verdict = "HIGH_RISK" if score >= 60 else "CAUTION" if score >= 30 else "LOOKS_OK"
    return {"score": score, "verdict": verdict, "reasons": reasons,
            "price_ratio": None if ratio is None else round(ratio, 2)}
