import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.market_data import MarketDataLoader
from app.services.data_cleaner import DataCleaner
from app.backtesting.engine import BacktestEngine
from app.backtesting.metrics import PerformanceMetrics

def run_phase6_test():
    print("--- Strategy Risk & Performance Analytics ---")
    
    loader = MarketDataLoader()
    raw_df = loader.fetch_history("AAPL", "2021-01-01", "2023-12-31")
    cleaned_df, _ = DataCleaner.clean(raw_df)

    engine = BacktestEngine(initial_capital=10000.0, commission=0.001, slippage=0.0005)
    results = engine.run_ma_crossover(cleaned_df, short_window=20, long_window=50)

    # Calculate metrics
    strategy_metrics = PerformanceMetrics.calculate_metrics(results, equity_col="Strategy_Equity", return_col="Strategy_Return")
    benchmark_metrics = PerformanceMetrics.calculate_metrics(results, equity_col="Benchmark_Equity", return_col="Asset_Return")

    print("\n[Strategy vs Benchmark Breakdown]")
    print(f"{'Metric':<24} | {'Strategy':<12} | {'Benchmark (Buy & Hold)':<12}")
    print("-" * 58)
    for key in strategy_metrics.keys():
        s_val = strategy_metrics.get(key, "N/A")
        b_val = benchmark_metrics.get(key, "N/A")
        print(f"{key:<24} | {str(s_val):<12} | {str(b_val):<12}")

if __name__ == "__main__":
    run_phase6_test()
