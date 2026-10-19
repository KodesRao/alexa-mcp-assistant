"""ShopShield MCP server for Alexa+ (Day 1 starter).

Transport: Streamable HTTP at http://<host>:8000/mcp
Run:       python server.py
"""

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from rules import assess_deal, assess_store

mcp = FastMCP(
    "shopshield",
    instructions=(
        "ShopShield checks online shopping deals and stores for scam and counterfeit "
        "warning signs. Read the spoken_summary field to the customer. Never call a "
        "seller a scammer; describe risk signals only."
    ),
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000")),
)


@mcp.tool()
def check_deal(
    product: str,
    price: float,
    usual_price: float | None = None,
    seller_name: str = "",
    store_url: str = "",
    listing_text: str = "",
    payment_method: str = "",
    brand: str = "",
) -> dict[str, Any]:
    """Check an online shopping deal for scam or counterfeit warning signs.

    Use when a customer asks if a deal, listing, or seller looks legit.
    Returns a risk level (low, medium, high), the signals found, and a
    short spoken_summary to read aloud.
    """
    return assess_deal(product, price, usual_price, seller_name, store_url,
                       listing_text, payment_method, brand)


@mcp.tool()
def check_store(store_url: str, brand: str = "") -> dict[str, Any]:
    """Check an online store's web address for lookalike or risky-domain signs.

    Use when a customer asks if a website or shop link is safe to buy from.
    Optionally pass the brand the store claims to sell.
    """
    return assess_store(store_url, brand)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
