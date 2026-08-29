import re
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import requests
from services.market_data import MarketDataLoader

router = APIRouter(prefix="/api/market", tags=["Market Data"])

KNOWN_STOCKS = [
    {"symbol": "ITC", "name": "ITC Limited", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "ITC.NS", "tradingViewSymbol": "NSE:ITC"},
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "RELIANCE.NS", "tradingViewSymbol": "NSE:RELIANCE"},
    {"symbol": "TCS", "name": "Tata Consultancy Services", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "TCS.NS", "tradingViewSymbol": "NSE:TCS"},
    {"symbol": "INFY", "name": "Infosys Limited", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "INFY.NS", "tradingViewSymbol": "NSE:INFY"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "HDFCBANK.NS", "tradingViewSymbol": "NSE:HDFCBANK"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "ICICIBANK.NS", "tradingViewSymbol": "NSE:ICICIBANK"},
    {"symbol": "SBIN", "name": "State Bank of India", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "SBIN.NS", "tradingViewSymbol": "NSE:SBIN"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "BHARTIARTL.NS", "tradingViewSymbol": "NSE:BHARTIARTL"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "LT.NS", "tradingViewSymbol": "NSE:LT"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "MARUTI.NS", "tradingViewSymbol": "NSE:MARUTI"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "TATAMOTORS.NS", "tradingViewSymbol": "NSE:TATAMOTORS"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "AXISBANK.NS", "tradingViewSymbol": "NSE:AXISBANK"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "KOTAKBANK.NS", "tradingViewSymbol": "NSE:KOTAKBANK"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd.", "market": "IN", "exchange": "NSE", "currency": "INR", "backendSymbol": "HINDUNILVR.NS", "tradingViewSymbol": "NSE:HINDUNILVR"},
    {"symbol": "AAPL", "name": "Apple Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "AAPL", "tradingViewSymbol": "NASDAQ:AAPL"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "MSFT", "tradingViewSymbol": "NASDAQ:MSFT"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "GOOGL", "tradingViewSymbol": "NASDAQ:GOOGL"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "AMZN", "tradingViewSymbol": "NASDAQ:AMZN"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "NVDA", "tradingViewSymbol": "NASDAQ:NVDA"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "META", "tradingViewSymbol": "NASDAQ:META"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "TSLA", "tradingViewSymbol": "NASDAQ:TSLA"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "NFLX", "tradingViewSymbol": "NASDAQ:NFLX"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "AMD", "tradingViewSymbol": "NASDAQ:AMD"},
    {"symbol": "INTC", "name": "Intel Corporation", "market": "US", "exchange": "NASDAQ", "currency": "USD", "backendSymbol": "INTC", "tradingViewSymbol": "NASDAQ:INTC"}
]

@router.get("/search")
def search_instruments(q: str = Query(..., min_length=1)):
    query = q.strip().upper()
    results = []
    seen = set()

    # 1. First search in curated known stocks
    for s in KNOWN_STOCKS:
        sym = s["symbol"].upper()
        name = s["name"].upper()
        if sym.startswith(query) or query in sym or query in name:
            results.append(s)
            seen.add(s["symbol"])

    # 2. Query Yahoo Finance API for broader universe
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=15&newsCount=0"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            quotes = resp.json().get("quotes", [])
            for quote in quotes:
                quote_type = quote.get("quoteType", "")
                if quote_type not in ("EQUITY", "ETF"):
                    continue

                raw_symbol = quote.get("symbol", "").strip().upper()
                if not raw_symbol or "^" in raw_symbol:
                    continue

                exchange_disp = (quote.get("exchDisp") or quote.get("exchange") or "").upper()
                name = quote.get("shortname") or quote.get("longname") or raw_symbol

                is_nse = raw_symbol.endswith(".NS") or exchange_disp in ("NSE", "NSI")
                is_bse = raw_symbol.endswith(".BO") or exchange_disp in ("BSE", "BOM")

                if is_nse:
                    clean_symbol = re.sub(r"\.NS$", "", raw_symbol, flags=re.IGNORECASE)
                    market = "IN"
                    exchange = "NSE"
                    currency = "INR"
                    backend_symbol = f"{clean_symbol}.NS"
                    tv_symbol = f"NSE:{clean_symbol}"
                elif is_bse:
                    clean_symbol = re.sub(r"\.BO$", "", raw_symbol, flags=re.IGNORECASE)
                    market = "IN"
                    exchange = "BSE"
                    currency = "INR"
                    backend_symbol = f"{clean_symbol}.BO"
                    tv_symbol = f"BSE:{clean_symbol}"
                else:
                    clean_symbol = raw_symbol
                    market = "US"
                    exchange = "NASDAQ" if any(x in exchange_disp for x in ("NAS", "NMS", "NGS")) else ("NYSE" if "NY" in exchange_disp else "NASDAQ")
                    currency = "USD"
                    backend_symbol = clean_symbol
                    tv_symbol = f"{exchange}:{clean_symbol}"

                if clean_symbol in seen:
                    continue

                seen.add(clean_symbol)
                results.append({
                    "symbol": clean_symbol,
                    "name": name,
                    "market": market,
                    "exchange": exchange,
                    "currency": currency,
                    "backendSymbol": backend_symbol,
                    "tradingViewSymbol": tv_symbol
                })
    except Exception:
        pass

    # Sort results: Exact ticker match first, then starts-with, then name matches
    def rank_key(item):
        sym = item["symbol"].upper()
        name = item["name"].upper()
        if sym == query:
            return 0
        if sym.startswith(query):
            return 1
        if name.startswith(query):
            return 2
        return 3

    results.sort(key=rank_key)
    return results[:20]

@router.get("/history/{ticker}")
def fetch_history(ticker: str, start: str = "2021-01-01", end: str = "2023-12-31"):
    try:
        loader = MarketDataLoader()
        df = loader.fetch_history(ticker, start, end)
        return df.reset_index().to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
