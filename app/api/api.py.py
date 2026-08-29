# api.py
import io
import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow your frontend to talk to your backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_stock_data(ticker: str, interval: str, period: str):
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    if df.empty:
        return pd.DataFrame()
    
    df = df.reset_index()
    if "Date" in df.columns:
         df.rename(columns={"Date": "Datetime"}, inplace=True)
            
    df["Return_%"] = df["Close"].pct_change() * 100
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    return df.dropna()

@app.get("/api/stock-data")
def fetch_data_json(ticker: str = "NVDA", interval: str = "15m", period: str = "60d"):
    """Returns JSON data to populate your HTML table."""
    df = get_stock_data(ticker, interval, period)
    if df.empty:
        return {"error": "No data found"}
    # Return data as a list of dictionaries for the frontend table
    return df.to_dict(orient="records")

@app.get("/api/download/csv")
def download_csv(ticker: str = "NVDA", interval: str = "15m", period: str = "60d"):
    """Returns a CSV file download."""
    df = get_stock_data(ticker, interval, period)
    csv_data = df.to_csv(index=False)
    return Response(
        content=csv_data, 
        media_type="text/csv", 
        headers={"Content-Disposition": f"attachment; filename={ticker}_data.csv"}
    )
