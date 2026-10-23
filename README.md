# ShopShield: shopping scam protection for Alexa+ (MCP server)

**Demo video:** https://youtu.be/E6jl3r7TDik

An MCP server (streamable HTTP, endpoint `/mcp`) that helps shoppers avoid scams and fake products. Voice-first: every tool returns a short `speech` field plus details.

(keep your Tools table and Design paragraph exactly as they are)

## Run it (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then put your Gemini key in .env
python test_heuristics.py   # should print "ok" x7
python server.py            # serves http://localhost:8000/mcp
```

Get a free key at https://aistudio.google.com/apikey

No key yet? Test the wiring with fake data: `SHOPSHIELD_OFFLINE=1 python server.py`

## Expose the server with a tunnel

Alexa+ needs a public HTTPS address. Download `cloudflared` for your Mac from Cloudflare, make it executable (`chmod +x cloudflared`), then run this in a second terminal:

```bash
./cloudflared tunnel --url http://localhost:8000
```

It prints an address like `https://<random-words>.trycloudflare.com`. Your MCP server URL is that address followed by `/mcp`. Keep both terminals open while demoing. The address changes each time you restart the tunnel.

## Test it

In a third terminal (with the virtual environment active), run the test client against your tunnel address:

```bash
python test_client.py https://<your-tunnel-address>/mcp
```

It connects over MCP, lists the tools, and runs four demo calls, printing the `speech` line for each result.

## Demo script (voice)

1. "Is a Nike Air Max 90 for 90 ringgit on Shopee legit?"
2. "Check this title: N.i.k.e Air Max 1:1 OEM"
3. "Is 300 ringgit a real discount if it says 900 ringgit before?"

## Troubleshooting

- `421` / invalid host through a tunnel: already handled (`transport_security` in `server.py`).
- `429` from Gemini: live price search with Google Search needs paid quota, and the free tier returns this error. Workaround: pass the shopper's stated `official_price` to `scam_risk_verdict` or `is_real_discount`, and the server skips the live lookup. `find_official_price` and `compare_prices` need that quota.
- `ModuleNotFoundError: mcp.server.fastmcp`: you got mcp 2.x. Run `pip install "mcp[cli]<2"`.
