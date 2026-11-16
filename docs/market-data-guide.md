# Market data: freshness and troubleshooting

The dashboard embeds third-party TradingView charts for USD/CNY, NASDAQ-100, S&P 500, spot gold, BTC/USD, and the Shanghai Composite. It does not generate simulated prices or require a paid API key.

## Before interpreting a quote

- Check the exchange session and the timestamp shown by the chart provider. Market closures and provider-specific delays can make a quote look stale.
- NASDAQ:NDX tracks the **NASDAQ-100**, not the Nasdaq Composite.
- FX, gold, and BTC may have different trading sessions and data-provider conventions.
- Compare prices only after checking the quote currency, instrument and timestamp.

## If a chart is blank

1. Check network access to TradingView and disable script blockers for the site if appropriate.
2. Reload the page and try a different network or browser.
3. Open the symbol directly on TradingView to distinguish an embed problem from unavailable upstream data.
4. Do not substitute fabricated numbers when a widget is unavailable.

## Privacy

The public site must not contain portfolio holdings, balances, personal account information, API secrets, or private financial data. Embedded charts are loaded from a third party and follow that provider's data and privacy policies.
