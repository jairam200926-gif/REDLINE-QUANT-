import yfinance as yf
import pandas as pd
from pathlib import Path

class MarketDataLoader:
    def __init__(self, data_dir: str = "../../data"):
        self.data_dir = Path(__file__).parent.joinpath(data_dir).resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_history(self, symbol: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
        symbol = symbol.upper()
        file_name = f"{symbol}_{start_date}_{end_date}_{interval}.csv"
        file_path = self.data_dir / file_name

        if file_path.exists():
            print(f"[{symbol}] Loading data from local cache...")
            return pd.read_csv(file_path, index_col=0, parse_dates=True)

        print(f"[{symbol}] Downloading data from Yahoo Finance...")
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=interval)
            
            if df.empty:
                raise ValueError(f"No data found for symbol '{symbol}'.")
                
            df.index = df.index.tz_localize(None)
            df.to_csv(file_path)
            print(f"[{symbol}] Saved data to cache at {file_path}")
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()