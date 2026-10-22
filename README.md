# ShopShield: shopping scam protection for Alexa+ (MCP server)

An MCP server (streamable HTTP, endpoint `/mcp`) that helps shoppers avoid scams and fake products.
Voice-first: every tool returns a short `speech` field plus details.

## Tools
| Tool | What it does |
|---|---|
| `find_official_price` | Official brand-store price (Gemini + Google Search) |
| `compare_prices` | Official vs marketplace prices (Shopee, Lazada) |
| `check_listing_wording` | Counterfeit signs in a title: disguised brand names, "1:1/OEM/AAA", hidden characters |
| `scam_risk_verdict` | Wording checks + price vs official price, returns a 0-100 risk score |
| `is_real_discount` | Checks a claimed "original price" against the official price |

Design: wording and scoring are **deterministic code** (`heuristics.py`), so they are fast and repeatable.
Gemini is used only to research prices (`gemini_client.py`). Results are cached to protect free-tier quota.

## Run it (macOS)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your Gemini key in .env
python test_heuristics.py   # should print "ok" x7
python server.py            # serves http://localhost:8000/mcp
```
Get a free key at https://aistudio.google.com/apikey

No key yet? Test the wiring with fake data: `SHOPSHIELD_OFFLINE=1 python server.py`

## Test with MCP Inspector
```bash
npx @modelcontextprotocol/inspector
```
Transport = Streamable HTTP, URL = `http://localhost:8000/mcp`, Connect, Tools, run `scam_risk_verdict`.

## Expose to Alexa+
```bash
brew install ngrok
ngrok http 8000
```
Use `https://<your-id>.ngrok-free.app/mcp` as the MCP server URL in the Alexa+ / Devpost setup.
Follow the hackathon resources page for the exact registration steps. Keep both terminals open while demoing.

## Demo script (voice)
1. "Is a Nike Air Max 90 for 90 ringgit on Shopee legit?"
2. "Check this title: N.i.k.e Air Max 1:1 OEM"
3. "Is 300 ringgit a real discount if it says 900 ringgit before?"
4. "Compare prices for the Sony WH-1000XM5."

## Troubleshooting
- `421` / invalid host through ngrok: already handled (`transport_security` in `server.py`).
- `429` from Gemini: free-tier limit. Wait a minute, or use the cache by repeating the same product.
- `ModuleNotFoundError: mcp.server.fastmcp`: you got mcp 2.x. Run `pip install "mcp[cli]<2"`.

## Ideas to extend (if time)
Add brands to `BRANDS` in `heuristics.py`; add seller-age or review-count inputs to the score;
add an API-key header check before public use.
