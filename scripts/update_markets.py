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

def request_chart(symbol, range_, interval):
    code = urllib.parse.quote(symbol, safe="")
    error = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        url = f"https://{host}/v8/finance/chart/{code}?range={range_}&interval={interval}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=18) as res:
                result = json.load(res)["chart"]["result"][0]
            return result
        except Exception as exc:
            error = str(exc)
            time.sleep(1)
    raise RuntimeError(error)

def extract(result):
    stamps = result.get("timestamp") or []
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, stamp in enumerate(stamps):
        vals = {k: quote[k][i] for k in ("open", "high", "low", "close")}
        if any(v is None for v in vals.values()):
            continue
        rows.append({"date": dt.datetime.fromtimestamp(stamp, dt.timezone.utc).isoformat(),
                     **{k: round(v, 5) for k, v in vals.items()}})
    return rows

def aggregate(rows, mode):
    grouped = {}
    for row in rows:
        date = dt.date.fromisoformat(row["date"][:10])
        if mode == "weekly":
            key = (date - dt.timedelta(days=date.weekday())).isoformat()
        else:
            key = date.replace(day=1).isoformat()
        if key not in grouped:
            grouped[key] = {"date": key, **{k: row[k] for k in ("open", "high", "low", "close")}}
        else:
            current = grouped[key]
            current["high"] = max(current["high"], row["high"])
            current["low"] = min(current["low"], row["low"])
            current["close"] = row["close"]
    return list(grouped.values())

def fetch(symbol):
    historical = request_chart(symbol, "5y", "1d")
    daily = extract(historical)
    if len(daily) < 10:
        raise ValueError("Insufficient historical observations")
    weekly = aggregate(daily, "weekly")
    monthly = aggregate(daily, "monthly")
    result = {"symbol": symbol, "currency": historical.get("meta", {}).get("currency"),
              "lastMarketTimestamp": historical["timestamp"][-1],
              "daily": daily, "weekly": weekly, "monthly": monthly}
    try:
        intraday = request_chart(symbol, "1d", "5m")
        result["intraday"] = extract(intraday)
    except Exception as exc:
        print(f"Intraday unavailable for {symbol}: {exc}")
        result["intraday"] = []
    return result

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
