#!/usr/bin/env python3
"""Fetch public Yahoo Finance chart data for a static, no-client-API dashboard.
Unofficial endpoint: availability is not guaranteed. Never manufacture quotes.
"""
import datetime as dt
import json
import math
import os
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
SOURCE_LABELS = {"Yahoo Finance": "Yahoo Finance (unofficial)", "Eastmoney / AKShare": "Eastmoney via AKShare"}
UNITS = {"usdcny": "CNY per USD", "nasdaq": "index points", "sp500": "index points", "gold": "USD per troy ounce (COMEX futures)", "btc": "USD per BTC", "sse": "index points"}

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
    result["source"] = "Yahoo Finance"
    return result

def fetch_eastmoney_sse():
    """Only use the unambiguous Shanghai Composite index, never a similarly named security."""
    import akshare as ak
    today = dt.datetime.now(dt.timezone.utc).date()
    start = (today - dt.timedelta(days=5*366)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")
    frame = ak.index_zh_a_hist(symbol="000001", period="daily", start_date=start, end_date=end)
    if frame is None or frame.empty:
        raise ValueError("Eastmoney returned no Shanghai Composite history")
    required = ("日期", "开盘", "最高", "最低", "收盘")
    if any(column not in frame.columns for column in required):
        raise ValueError("Unexpected Eastmoney response columns")
    rows = []
    for _, record in frame.iterrows():
        date = str(record["日期"])[:10]
        dt.date.fromisoformat(date)
        values = {field: float(record[column]) for field, column in (("open", "开盘"), ("high", "最高"), ("low", "最低"), ("close", "收盘"))}
        if not all(math.isfinite(v) and v > 0 for v in values.values()):
            continue
        if values["low"] > min(values["open"], values["close"]) or values["high"] < max(values["open"], values["close"]):
            continue
        rows.append({"date": date, **{k: round(v, 5) for k, v in values.items()}})
    rows.sort(key=lambda item: item["date"])
    if len(rows) < 100 or len({row["date"] for row in rows}) != len(rows):
        raise ValueError("Eastmoney data has insufficient or duplicate dates")
    latest = dt.datetime.combine(dt.date.fromisoformat(rows[-1]["date"]), dt.time(15, 0), dt.timezone(dt.timedelta(hours=8)))
    return {"symbol": "000001.SS", "sourceSymbol": "000001", "source": "Eastmoney / AKShare", "currency": "CNY", "lastMarketTimestamp": int(latest.timestamp()), "daily": rows, "weekly": aggregate(rows, "weekly"), "monthly": aggregate(rows, "monthly"), "intraday": []}

def validate_market(key, data):
    if data.get("symbol") != SYMBOLS[key]:
        raise ValueError(f"Symbol mismatch for {key}: {data.get('symbol')}")
    if data.get("source") == "Eastmoney / AKShare" and key != "sse":
        raise ValueError("Unverified Eastmoney mapping")
    rows = data.get("daily") or []
    if len(rows) < 100:
        raise ValueError("Insufficient daily observations")
    for row in rows:
        o,h,l,c = (float(row[k]) for k in ("open","high","low","close"))
        dt.date.fromisoformat(row["date"][:10])
        if not all(math.isfinite(v) and v > 0 for v in (o,h,l,c)) or l > min(o,c) or h < max(o,c):
            raise ValueError("Invalid OHLC values")
    dates = [row["date"][:10] for row in rows]
    if dates != sorted(set(dates)):
        raise ValueError("Unsorted or duplicate dates")
    data["unit"] = UNITS[key]
    data.setdefault("source", "Yahoo Finance")
    data.setdefault("sourceSymbol", SYMBOLS[key])
    return data

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
            if key == "sse":
                try:
                    markets[key] = validate_market(key, fetch_eastmoney_sse())
                except Exception as em_error:
                    print(f"Eastmoney failed for {key}: {em_error}; trying Yahoo Finance")
                    markets[key] = validate_market(key, fetch(symbol))
            else:
                markets[key] = validate_market(key, fetch(symbol))
            print(f"OK {key}: {len(markets[key]['weekly'])} weeks")
        except Exception as exc:
            errors[key] = str(exc)
            print(f"ERROR {key}: {exc}")
            if key in old:
                try:
                    markets[key] = validate_market(key, old[key])  # preserve original timestamp and source
                    markets[key]["cached"] = True
                except Exception as cached_error:
                    print(f"Invalid cache {key}: {cached_error}")
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
