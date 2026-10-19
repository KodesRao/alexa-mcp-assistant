"""End-to-end check: connect over Streamable HTTP, list tools, call each tool.

Start the server first (python server.py), then run: python test_client.py
"""

import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_URL = "http://127.0.0.1:8000/mcp"


async def main() -> None:
    async with streamablehttp_client(SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print("Negotiated protocol version:", init.protocolVersion)

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            deal = await session.call_tool("check_deal", {
                "product": "Nike Air Jordan 1",
                "price": 45,
                "usual_price": 180,
                "store_url": "nike-outlet-sale.shop",
                "brand": "nike",
                "listing_text": "1:1 quality, only today!",
                "payment_method": "bank transfer",
            })
            print("\ncheck_deal (risky):")
            print(json.dumps(deal.structuredContent, indent=2))

            store = await session.call_tool("check_store", {"store_url": "https://www.nike.com"})
            print("\ncheck_store (official):")
            print(json.dumps(store.structuredContent, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
