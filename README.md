# LAOXU MARKET

Public six-market dashboard: https://finance.laoxu.org

## Markets and verified identifiers

| Market | Yahoo Finance symbol | Note |
|---|---|---|
| USD/CNY | `CNY=X` | FX |
| Nasdaq-100 | `^NDX` | Nasdaq-100, not Nasdaq Composite |
| S&P 500 | `^GSPC` | Index |
| Gold | `GC=F` | COMEX gold futures, **not spot XAU/USD** |
| Bitcoin USD | `BTC-USD` | Crypto |
| Shanghai Composite | `000001.SS` | SSE index |

The browser checks each JSON payload's symbol against the expected identifier. Mismatches are not rendered.

## Plan A: market reliability

- Six full-width responsive candlestick charts, always **weekly** candles.
- One shared range selector: 1 month, 1 year, 3 years, 5 years.
- Latest daily change overview uses a public edge quote when valid and recent; otherwise falls back to the last daily close from the published snapshot with its date visible.
- Per-chart status includes source symbol, timestamp, cached/failed status and staleness warning.
- No simulated quotes or candles. If data is unavailable, an error is displayed.
- Historical data: GitHub Actions runs `scripts/update_markets.py` every 3 hours (schedule is best effort), retrieving the **unofficial** Yahoo Finance public chart endpoint. Quotes may be delayed or unavailable.
- Optional live quote endpoint: `https://quotes.laoxu.org/api/quotes`; if unavailable the dashboard continues using the published snapshot.

## Privacy

The repository contains no holdings, balances, account details, credentials or personal financial information. Public third-party quote requests still expose ordinary web request metadata (such as IP address) to their providers.

## GitHub Pages deployment

`.github/workflows/deploy.yml` deploys on every push to `main` or manual dispatch. `.github/workflows/market-data.yml` updates public market snapshots and deploys the refreshed site on a scheduled or manual run.

In repository **Settings → Pages**, choose **GitHub Actions** as the build and deployment source. Cloudflare CNAME: `finance` → `xyh421.github.io` (DNS only). Custom domain is configured by root `CNAME` file.

No paid API key required. Data availability is not guaranteed by Yahoo Finance.
