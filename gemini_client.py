"""Gemini helpers: a grounded (Google Search) research call, then a structured-JSON call."""
import os
import time
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OFFLINE = os.getenv("SHOPSHIELD_OFFLINE", "0") == "1"
_client = None
_cache: dict[tuple[str, str], dict] = {}  # saves free-tier quota during demos


class PriceInfo(BaseModel):
    official_price: float | None = None
    currency: str | None = None
    official_source: str | None = None
    market_low: float | None = None
    market_median: float | None = None
    market_high: float | None = None
    confidence: str = "low"  # low | medium | high
    note: str = ""


def _get_client():
    global _client
    if _client is None:
        from google import genai
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set. Copy .env.example to .env and add it.")
        _client = genai.Client(api_key=key)
    return _client


def _call(retry=True, **kwargs):
    """One retry on rate limit (free tier is tight)."""
    try:
        return _get_client().models.generate_content(model=MODEL, **kwargs)
    except Exception as e:  # noqa: BLE001
        if retry and ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)):
            time.sleep(8)
            return _get_client().models.generate_content(model=MODEL, **kwargs)
        raise


def grounded_search(prompt: str) -> tuple[str, list[str]]:
    from google.genai import types
    resp = _call(
        retry=False,
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,
        ),
    )
    sources: list[str] = []
    try:
        for ch in resp.candidates[0].grounding_metadata.grounding_chunks or []:
            if ch.web and ch.web.uri and ch.web.uri not in sources:
                sources.append(ch.web.uri)
    except (AttributeError, IndexError, TypeError):
        pass
    return resp.text or "", sources[:5]


def structure_prices(research_text: str) -> PriceInfo:
    from google.genai import types
    resp = _call(
        contents=(
            "Extract price facts from the research notes below. Use only numbers that appear "
            "in the notes. If a value is not stated, use null. official_price is the price at "
            "the brand's own official store or website. market_* are typical prices on "
            "marketplaces (Shopee, Lazada, etc.). Prices are plain numbers in the local "
            "currency, no symbols.\n\nNOTES:\n" + research_text
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PriceInfo,
            temperature=0,
        ),
    )
    if resp.parsed is not None:
        return resp.parsed
    return PriceInfo.model_validate_json(resp.text)


def research_prices(product: str, country: str = "MY") -> dict:
    """Find official-store and marketplace prices. Returns dict with PriceInfo fields + sources."""
    key = (product.strip().lower(), country.upper())
    if key in _cache:
        return _cache[key]

    if OFFLINE:
        data = PriceInfo(official_price=429.0, currency="MYR",
                         official_source="offline-demo", market_low=250.0,
                         market_median=399.0, market_high=450.0, confidence="low",
                         note="OFFLINE DEMO DATA, not real prices").model_dump()
        data["sources"] = []
        return data

    text, sources = grounded_search(
        f"Find current prices in country code {country} for: {product}.\n"
        "1) The price at the brand's OFFICIAL store or official website.\n"
        "2) Typical prices on marketplaces such as Shopee and Lazada (low, median, high).\n"
        "State the currency. Be brief. If you cannot find a number, say so; never guess."
    )
    info = structure_prices(text)
    data = info.model_dump()
    data["sources"] = sources
    _cache[key] = data
    return data
