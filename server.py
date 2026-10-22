"""ShopShield MCP server: shopping scam and counterfeit protection for Alexa+.

Transport: streamable HTTP, endpoint /mcp.  Run:  python server.py
"""
import os
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

import heuristics
from gemini_client import research_prices

mcp = FastMCP(
    "shopshield",
    instructions=(
        "ShopShield helps shoppers avoid scams and fake products. Use it when the user asks "
        "if a listing is legit, if a price is real, or where to buy something cheaper. "
        "Always read the 'speech' field aloud first; keep answers short."
    ),
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
    # Allow requests that come through an ngrok / cloudflared tunnel hostname.
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

CURRENCY_WORDS = {"MYR": "ringgit", "SGD": "Singapore dollars", "USD": "dollars",
                  "IDR": "rupiah", "THB": "baht", "PHP": "pesos", "VND": "dong"}


COUNTRY_CURRENCY = {"MY": "MYR", "SG": "SGD", "ID": "IDR", "TH": "THB",
                    "PH": "PHP", "VN": "VND", "US": "USD"}


def _get_price(product: str, country: str, official_price: float | None = None):
    """Use the price the shopper stated if given; otherwise try the live lookup."""
    if official_price is not None:
        return {"official_price": official_price,
                "currency": COUNTRY_CURRENCY.get(country.upper(), "MYR"),
                "official_source": "stated by shopper", "market_low": None,
                "market_median": None, "market_high": None, "confidence": "high",
                "note": "", "sources": []}, None
    return _safe_research(product, country)


def _money(value: float | None, currency: str | None) -> str:
    if value is None:
        return "unknown"
    word = CURRENCY_WORDS.get((currency or "").upper(), currency or "")
    return f"{value:,.0f} {word}".strip()


def _safe_research(product: str, country: str) -> tuple[dict | None, str | None]:
    try:
        return research_prices(product, country), None
    except Exception as e:  # noqa: BLE001
        return None, f"price lookup failed: {type(e).__name__}"


@mcp.tool()
def find_official_price(product: str, country: str = "MY") -> dict:
    """Find the price of a product at the brand's official store.
    Use when the shopper asks what something should cost or what the official price is.
    country is a 2-letter code such as MY, SG, ID, TH, PH, VN, US."""
    info, err = _safe_research(product, country)
    if err or not info:
        return {"speech": f"Sorry, I could not look up {product} right now.", "error": err}
    if info["official_price"] is None:
        return {"speech": f"I could not find an official price for {product}.", **info}
    speech = (f"The official price for {product} is about "
              f"{_money(info['official_price'], info['currency'])}.")
    return {"speech": speech, **info}


@mcp.tool()
def compare_prices(product: str, country: str = "MY") -> dict:
    """Compare the official-store price with typical marketplace prices (Shopee, Lazada).
    Use when the shopper wants to know where it is cheaper or what a fair price is."""
    info, err = _safe_research(product, country)
    if err or not info:
        return {"speech": f"Sorry, I could not compare prices for {product} right now.",
                "error": err}
    cur = info["currency"]
    parts = []
    if info["official_price"] is not None:
        parts.append(f"official store about {_money(info['official_price'], cur)}")
    if info["market_median"] is not None:
        parts.append(f"marketplaces usually around {_money(info['market_median'], cur)}")
    if info["market_low"] is not None:
        parts.append(f"lowest seen {_money(info['market_low'], cur)}")
    speech = (f"For {product}: " + ", ".join(parts) + ".") if parts else \
        f"I could not find reliable prices for {product}."
    return {"speech": speech, **info}


@mcp.tool()
def check_listing_wording(title: str) -> dict:
    """Check a listing title for counterfeit signs only (disguised brand names, fake-goods
    wording, hidden characters). Fast, no price lookup."""
    r = heuristics.analyze_listing(title)
    if r["reasons"]:
        speech = f"{r['verdict'].replace('_', ' ').title()}: " + "; ".join(r["reasons"]) + "."
    else:
        speech = "The wording looks normal."
    return {"speech": speech, **r}


@mcp.tool()
def scam_risk_verdict(title: str, listed_price: float, official_price: float | None = None,
                      product_name: str = "", platform: str = "", country: str = "MY") -> dict:
    """Decide how risky a marketplace listing is. Combines wording checks with a price
    comparison against the official store. Use when the shopper asks 'is this legit?'.
    title is the listing title, listed_price is the seller's price as a number,
    official_price is the brand's official price if the shopper states it (pass it when known).
    product_name is the real product if known (e.g. 'Nike Air Max 90')."""
    info, err = _get_price(product_name or title, country, official_price)
    official = info["official_price"] if info else None
    cur = info["currency"] if info else None
    r = heuristics.analyze_listing(title, listed_price, official)

    label = {"HIGH_RISK": "High risk", "CAUTION": "Be careful", "LOOKS_OK": "Looks okay"}[r["verdict"]]
    speech = f"{label}. Risk score {r['score']} out of 100."
    if r["reasons"]:
        speech += " " + "; ".join(r["reasons"][:3]).capitalize() + "."
    if official is None:
        speech += (" I could not look up the official price. Tell me the official price "
                   "and I can check again.")
    elif r["verdict"] != "LOOKS_OK":
        speech += f" The official price is about {_money(official, cur)}."
    if r["verdict"] == "HIGH_RISK":
        speech += " I would not buy this."
    return {"speech": speech, "platform": platform, "listed_price": listed_price,
            "official_price": official, "currency": cur,
            "sources": (info or {}).get("sources", []), "lookup_error": err, **r}


@mcp.tool()
def is_real_discount(product: str, sale_price: float, claimed_original_price: float,
                     official_price: float | None = None, country: str = "MY") -> dict:
    """Check if a 'sale' is genuine. Compares the claimed original price and the sale price
    with the official-store price. Use when the shopper asks 'is this a real discount?'.
    official_price is the brand's official price if the shopper states it (pass it when known)."""
    info, err = _get_price(product, country, official_price)
    if err or not info or info["official_price"] is None:
        claimed_off = round((1 - sale_price / claimed_original_price) * 100)
        return {"speech": f"The listing claims {claimed_off} percent off, but I could not "
                          "confirm the official price. Tell me the official price and I can check.",
                "error": err}
    official, cur = info["official_price"], info["currency"]
    claimed_off = round((1 - sale_price / claimed_original_price) * 100)
    real_off = round((1 - sale_price / official) * 100)
    inflated = claimed_original_price > official * 1.15
    if inflated:
        speech = (f"Not a real discount. The listing says {claimed_off} percent off, but the "
                  f"official price is {_money(official, cur)}, so you really save {real_off} "
                  "percent." if real_off > 0 else
                  f"Not a real discount. The official price is {_money(official, cur)}, "
                  "which is lower than this sale price.")
    elif real_off > 0:
        speech = f"Yes, you save about {real_off} percent against the official price."
    else:
        speech = f"No saving. The official price is {_money(official, cur)}."
    return {"speech": speech, "claimed_discount_pct": claimed_off,
            "real_discount_pct": real_off, "original_price_inflated": inflated, **info}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
