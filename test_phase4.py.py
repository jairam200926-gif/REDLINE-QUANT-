import sys
import os
from pathlib import Path

# Force Python to locate the 'backend' folder
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.market_data import MarketDataLoader
from app.services.data_cleaner import DataCleaner
from app.analysis.eda import MarketAnalyzer
from app.analysis.indicators import TechnicalIndicators

def generate_analysis_download(symbol: str, start_date: str, end_date: str):
    print(f"--- Generating Full Analysis for {symbol} ---")
    
    loader = MarketDataLoader()
    raw_df = loader.fetch_history(symbol, start_date, end_date)
    
    cleaned_df, report = DataCleaner.clean(raw_df)
    
    analyzer = MarketAnalyzer()
    analyzed_df = analyzer.calculate_returns(cleaned_df)
    analyzed_df = analyzer.calculate_volatility(analyzed_df, window=20)
    
    indicators = TechnicalIndicators()
    final_df = indicators.add_sma(analyzed_df, window=20)
    final_df = indicators.add_sma(final_df, window=50)
    final_df = indicators.add_rsi(final_df, window=14)
    final_df = indicators.add_macd(final_df)
    
    export_dir = backend_dir / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    filename = export_dir / f"{symbol}_fully_analyzed.csv"
    final_df.to_csv(filename)
    
    print(f"Success! Fully analyzed data saved to: {filename}")
    print("\nFirst 5 rows of indicators:")
    print(final_df[["Close", "SMA_20", "SMA_50", "RSI_14", "MACD"]].iloc[50:55])

if __name__ == "__main__":
    generate_analysis_download("AAPL", "2022-01-01", "2023-12-31")