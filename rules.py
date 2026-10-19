"""ShopShield rule engine: deterministic scam and counterfeit signals.

Day 1 baseline. Each signal has an ID, a weight, and a plain-language reason.
On Day 2-3, an LLM (Amazon Bedrock) adds signals from free text on top of these rules.
"""

from difflib import SequenceMatcher
from urllib.parse import urlparse

# Official domains for a few sample brands. Extend as needed.
OFFICIAL_DOMAINS = {
    "nike": "nike.com",
    "adidas": "adidas.com",
    "apple": "apple.com",
    "samsung": "samsung.com",
    "sony": "sony.com",
    "lego": "lego.com",
    "dyson": "dyson.com",
    "rolex": "rolex.com",
}

UNSAFE_PAYMENT_TERMS = [
    "bank transfer", "wire transfer", "crypto", "bitcoin", "usdt",
    "gift card", "western union", "moneygram", "friends and family",
]
URGENCY_TERMS = [
    "only today", "today only", "limited time", "last chance", "hurry",
    "act now", "only 1 left", "only 2 left", "only 3 left", "ends tonight",
]
REPLICA_TERMS = [
    "replica", "1:1", "aaa quality", "mirror quality", "same factory",
    "oem quality", "inspired by", "dupe", "unbranded version",
]
RISKY_TLDS = [".shop", ".top", ".xyz", ".store", ".online", ".click", ".buzz", ".icu"]
DISCOUNT_WORDS = ["outlet", "sale", "discount", "clearance", "factory", "cheap"]


def _signal(signal_id: str, weight: int, reason: str) -> dict:
    return {"id": signal_id, "weight": weight, "reason": reason}


def _find_terms(text: str, terms: list[str]) -> list[str]:
    lowered = text.lower()
    return [t for t in terms if t in lowered]


def _risk_level(score: int) -> str:
    if score >= 5:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _spoken_summary(level: str, signals: list[dict]) -> str:
    """Short, voice-safe text. No URLs, no lists, at most three sentences."""
    if level == "low":
        return ("I didn't find common warning signs, but that is not a guarantee. "
                "Pay with a method that has buyer protection.")
    top = sorted(signals, key=lambda s: s["weight"], reverse=True)[:2]
    reasons = " and ".join(s["reason"] for s in top)
    opener = "This looks high risk." if level == "high" else "This has some warning signs."
    return (f"{opener} Main reasons: {reasons}. "
            "This is a risk check, not proof, so verify the seller before you pay.")


def assess_store(store_url: str, brand: str = "") -> dict:
    """Check a store URL for lookalike or risky-domain signals."""
    signals: list[dict] = []
    url = store_url if "://" in store_url else f"https://{store_url}"
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower().removeprefix("www.")

    if not host:
        return {"risk_level": "unknown", "score": 0, "signals": [],
                "spoken_summary": "I couldn't read that store address."}

    if parsed.scheme == "http":
        signals.append(_signal("NO_HTTPS", 1, "the site does not use a secure connection"))
    if host.replace(".", "").isdigit():
        signals.append(_signal("IP_ADDRESS_HOST", 3, "the store uses a raw IP address, not a name"))
    if any(host.endswith(tld) for tld in RISKY_TLDS):
        signals.append(_signal("RISKY_TLD", 1, "the web address ending is often used by short-lived shops"))
    if host.count("-") >= 2:
        signals.append(_signal("MANY_HYPHENS", 1, "the web address has an unusual pattern"))

    brands = [brand.lower()] if brand else list(OFFICIAL_DOMAINS)
    for b in brands:
        official = OFFICIAL_DOMAINS.get(b)
        if official and host == official:
            continue
        if b and b in host:
            words = _find_terms(host, DISCOUNT_WORDS)
            if words:
                signals.append(_signal("BRAND_PLUS_DISCOUNT_DOMAIN", 3,
                                       f"the address uses the {b} name with words like {words[0]}, "
                                       "a common counterfeit store pattern"))
            else:
                signals.append(_signal("BRAND_NOT_OFFICIAL_DOMAIN", 2,
                                       f"the address uses the {b} name but is not the official site"))
        elif official and SequenceMatcher(None, host, official).ratio() > 0.8:
            signals.append(_signal("TYPOSQUAT", 3,
                                   f"the address looks like a misspelling of the official {b} site"))

    score = sum(s["weight"] for s in signals)
    level = _risk_level(score)
    return {"host": host, "risk_level": level, "score": score, "signals": signals,
            "spoken_summary": _spoken_summary(level, signals)}


def assess_deal(product: str, price: float, usual_price: float | None = None,
                seller_name: str = "", store_url: str = "", listing_text: str = "",
                payment_method: str = "", brand: str = "") -> dict:
    """Check a deal for price, payment, urgency, and replica signals."""
    signals: list[dict] = []

    if usual_price and usual_price > 0 and price > 0:
        ratio = price / usual_price
        if ratio < 0.3:
            signals.append(_signal("PRICE_EXTREME", 3, "the price is more than 70 percent below normal"))
        elif ratio < 0.5:
            signals.append(_signal("PRICE_HIGH_DISCOUNT", 2, "the price is more than half off the normal price"))

    all_text = " ".join([product, seller_name, listing_text, payment_method])
    if pay := _find_terms(all_text, UNSAFE_PAYMENT_TERMS):
        signals.append(_signal("UNSAFE_PAYMENT", 3,
                               f"the seller wants payment by {pay[0]}, which has little buyer protection"))
    if _find_terms(all_text, URGENCY_TERMS):
        signals.append(_signal("URGENCY_PRESSURE", 1, "the listing uses pressure to buy quickly"))
    if rep := _find_terms(all_text, REPLICA_TERMS):
        signals.append(_signal("REPLICA_LANGUAGE", 3,
                               f"the listing uses the phrase {rep[0]}, which often means a counterfeit"))

    store = None
    if store_url:
        store = assess_store(store_url, brand)
        signals.extend(store["signals"])

    score = sum(s["weight"] for s in signals)
    level = _risk_level(score)
    return {"product": product, "risk_level": level, "score": score, "signals": signals,
            "store_host": store["host"] if store else None,
            "spoken_summary": _spoken_summary(level, signals)}
