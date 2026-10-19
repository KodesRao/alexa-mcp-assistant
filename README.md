# ShopShield: Safe Shopping for Alexa+

ShopShield is a self-hosted MCP server that lets Alexa+ check online deals and stores
for scam and counterfeit warning signs, and answer in short, voice-safe sentences.

> Built for the Build, Ship, Shape: Amazon Developer Hackathon (Alexa+ track).

## Tools

| Tool | What it does |
|------|--------------|
| `check_deal` | Checks price, payment method, urgency, and replica language in a deal. |
| `check_store` | Checks a store web address for lookalike and risky-domain patterns. |

Each tool returns a `risk_level` (low, medium, high), the `signals` it found, and a
`spoken_summary` for Alexa+ to read aloud. Results describe risk signals only. They do
not accuse any seller.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py                 # MCP endpoint: http://127.0.0.1:8000/mcp
```

In a second terminal:

```bash
python test_client.py            # lists tools and calls both of them
```

## Tech

- MCP spec 2025-11-25, Streamable HTTP transport (MCP Python SDK, FastMCP)
- Rule engine for deterministic signals (`rules.py`)
- Planned: Amazon Bedrock LLM layer for free-text signals

## Built during the hackathon

All code in this repository was written during the submission period.

## Known limits

- Brand matching uses simple substring checks, so a domain like `pineapple-shop.com`
  can match `apple`. To be fixed in the LLM layer.

## License

MIT
