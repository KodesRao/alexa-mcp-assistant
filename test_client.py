import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/mcp"

CALLS = [
    ("check_listing_wording", {"title": "N.i.k.e Air Max 1:1 OEM"}),
    ("scam_risk_verdict", {
        "title": "N.i.k.e Air Max 1:1 OEM",
        "listed_price": 90,
        "official_price": 429,
        "product_name": "Nike Air Max 90",
        "platform": "Shopee",
    }),
    ("scam_risk_verdict", {
        "title": "Nike Air Max 90 Men's Running Shoes",
        "listed_price": 410,
        "official_price": 429,
        "product_name": "Nike Air Max 90",
        "platform": "Shopee",
    }),
    ("is_real_discount", {
        "product": "Nike Air Max 90",
        "sale_price": 300,
        "claimed_original_price": 900,
        "official_price": 429,
    }),
]


async def main():
    print("Connecting to", URL)
    async with streamablehttp_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            for name, args in CALLS:
                print(f"\n--- {name} ---")
                result = await session.call_tool(name, args)
                data = json.loads(result.content[0].text)
                print("SPEECH:", data.get("speech"))
                if data.get("lookup_error") or data.get("error"):
                    print("PROBLEM:", data.get("lookup_error") or data.get("error"))


asyncio.run(main())