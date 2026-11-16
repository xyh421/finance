#!/usr/bin/env python3
"""Fetch public Yahoo Finance chart data for a static, no-client-API dashboard.
Unofficial endpoint: availability is not guaranteed. Never manufacture quotes.
"""
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request

SYMBOLS = {
    "usdcny": "CNY=X",
    "nasdaq": "^NDX",
    "sp500": "^GSPC",
    "gold": "GC=F",  # COMEX gold futures proxy, NOT XAUUSD spot
    "btc": "BTC-USD",
    "sse": "000001.SS",
}
OUT = pathlib.Path("data/markets.json")

def fetch(symbol):
    code = urllib.parse.quote(symbol, safe="")
    last_error = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{code}?range=2y&interval=1d"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; PublicMarketDashboard/1.0)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=18) as res:
                payload = json.load(res)
            result = payload["chart"]["result"][0]
            stamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]
            weekly = {}
            for i, stamp in enumerate(stamps):
                vals = {k: quotes[k][i] for k in ("open", "high", "low", "close")}
                if any(v is None for v in vals.values()):
                    continue
                day = dt.datetime.fromtimestamp(stamp, dt.timezone.utc).date()
                monday = day - dt.timedelta(days=day.weekday())
                key = monday.isoformat()
                if key not in weekly:
                    weekly[key] = {"date": key, **vals}
                else:
                    w = weekly[key]
                    w["high"] = max(w["high"], vals["high"])
                    w["low"] = min(w["low"], vals["low"])
                    w["close"] = vals["close"]
            rows = list(weekly.values())
            if len(rows) < 10:
                raise ValueError("Insufficient weekly observations")
            return {"symbol": symbol, "currency": result.get("meta", {}).get("currency"),
                    "lastMarketTimestamp": stamps[-1],
                    "weekly": [{k: (round(v, 5) if isinstance(v, float) else v) for k, v in row.items()} for row in rows]}
        except Exception as exc:
            last_error = str(exc)
            time.sleep(1)
    raise RuntimeError(last_error)

def main():
    old = {}
    if OUT.exists():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8")).get("markets", {})
        except (ValueError, OSError):
            pass
    markets = {}
    errors = {}
    for key, symbol in SYMBOLS.items():
        try:
            markets[key] = fetch(symbol)
            print(f"OK {key}: {len(markets[key]['weekly'])} weeks")
        except Exception as exc:
            errors[key] = str(exc)
            print(f"ERROR {key}: {exc}")
            if key in old:
                markets[key] = old[key]  # preserve timestamp of last successful fetch
    if not markets:
        raise SystemExit("No data available; refusing to publish an empty or fabricated snapshot")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "Yahoo Finance public chart endpoint (unofficial; may be delayed)",
        "markets": markets, "errors": errors
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if errors:
        print("Some feeds failed; previously cached data retained where available.")
if __name__ == "__main__":
    main()
