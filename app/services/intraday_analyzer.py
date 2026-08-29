"""Intraday analysis service adapted from the project's stock_analyzer.py."""

from __future__ import annotations

import pandas as pd
import yfinance as yf


class IntradayAnalyzer:
    @staticmethod
    def resolve_ticker(symbol: str) -> str:
        symbol = symbol.strip().upper()
        if "." in symbol:
            return symbol

        for candidate in (symbol, f"{symbol}.NS", f"{symbol}.BO"):
            try:
                if not yf.Ticker(candidate).history(period="1d").empty:
                    return candidate
            except Exception:
                continue
        return symbol

    @classmethod
    def analyze(cls, symbol: str) -> dict:
        ticker = cls.resolve_ticker(symbol)
        data = yf.download(ticker, period="60d", interval="15m", auto_adjust=False, progress=False)
        if data.empty:
            raise ValueError(f"No 15-minute market data was found for '{symbol}'.")
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        data = data.dropna()
        if len(data) < 50:
            raise ValueError("Not enough intraday data is available to calculate the strategy indicators.")

        data["Return"] = data["Close"].pct_change() * 100
        data["SMA20"] = data["Close"].rolling(20).mean()
        data["SMA50"] = data["Close"].rolling(50).mean()
        delta = data["Close"].diff()
        gains = delta.clip(lower=0).rolling(14).mean()
        losses = (-delta.clip(upper=0)).rolling(14).mean()
        data["RSI"] = 100 - (100 / (1 + gains / losses.replace(0, float("nan"))))
        daily = data.resample("D").agg({"High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna()
        daily["Return"] = daily["Close"].pct_change() * 100
        weekly = daily.resample("W").agg({"Close": "last", "Volume": "sum"}).dropna()
        weekly["Return"] = weekly["Close"].pct_change() * 100
        valid_daily = daily.dropna(subset=["Return"])
        valid_weekly = weekly.dropna(subset=["Return"])
        currency = "INR" if ticker.endswith((".NS", ".BO")) else "USD"
        dates = [index.strftime("%Y-%m-%d %H:%M") for index in data.index]

        return {
            "symbol": ticker,
            "currency": currency,
            "summary": {
                "last_price": round(float(data["Close"].iloc[-1]), 2),
                "high": round(float(data["High"].max()), 2),
                "low": round(float(data["Low"].min()), 2),
                "overall_return": round(float((data["Close"].iloc[-1] / data["Close"].iloc[0] - 1) * 100), 2),
                "best_day": valid_daily["Return"].idxmax().strftime("%d %b %Y"),
                "best_day_return": round(float(valid_daily["Return"].max()), 2),
                "worst_day": valid_daily["Return"].idxmin().strftime("%d %b %Y"),
                "worst_day_return": round(float(valid_daily["Return"].min()), 2),
                "best_week_return": round(float(valid_weekly["Return"].max()), 2),
            },
            "series": {
                "dates": dates,
                "close": [round(float(value), 2) for value in data["Close"]],
                "open": [round(float(value), 2) for value in data["Open"]],
                "high": [round(float(value), 2) for value in data["High"]],
                "low": [round(float(value), 2) for value in data["Low"]],
                "volume": [int(value) for value in data["Volume"]],
                "sma20": [None if pd.isna(value) else round(float(value), 2) for value in data["SMA20"]],
                "sma50": [None if pd.isna(value) else round(float(value), 2) for value in data["SMA50"]],
                "rsi": [None if pd.isna(value) else round(float(value), 2) for value in data["RSI"]],
                "daily_returns": [round(float(value), 2) for value in daily["Return"].fillna(0)],
            },
        }
