# LAOXU MARKET

Public finance dashboard at **https://finance.laoxu.org** (after GitHub Pages and DNS are configured).

## Market coverage (six only)

1. USD/CNY — `FX_IDC:USDCNY`
2. NASDAQ 100 — `NASDAQ:NDX` (NASDAQ-100; not Nasdaq Composite)
3. S&P 500 — `SP:SPX`
4. Spot gold XAU/USD — `OANDA:XAUUSD`
5. BTC/USD — `BITSTAMP:BTCUSD`
6. Shanghai Composite — `SSE:000001`

## Privacy

No personal holdings, balances, amounts, login, accounts, or private data. The homepage is static. Third-party TradingView embeds fetch market data from TradingView, subject to its own privacy policy, data availability and exchange delays. All six cards embed TradingView's free Mini Chart widget with third-party market quotes and charts. No mocked prices or simulated sparklines. Quotes may be delayed and widgets may be blocked by network restrictions. Click a card's detail button for the larger market chart.

## Deployment

1. In **Settings → Pages** set **Deploy from a branch**, branch **main**, folder **/(root)**.
2. In **Settings → Pages → Custom domain** enter `finance.laoxu.org` and save.
3. In Cloudflare DNS create a CNAME: name `finance`, target `xyh421.github.io`; start with DNS only (grey cloud).
4. Wait for GitHub's DNS verification and certificate provisioning, then enable **Enforce HTTPS**.

Website is pure HTML/CSS/JS; no build step or paid API key. The root `CNAME` file is included in the repository. Do not put secrets into this public repository.
