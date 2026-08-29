import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.market_data import MarketDataLoader
from app.services.data_cleaner import DataCleaner
from app.backtesting.engine import BacktestEngine

def run_backtest_test():
    print("--- Running Strategy Backtest ---")
    
    loader = MarketDataLoader()
    raw_df = loader.fetch_history("AAPL", "2021-01-01", "2023-12-31")
    cleaned_df, _ = DataCleaner.clean(raw_df)

    engine = BacktestEngine(initial_capital=10000.0, commission=0.001, slippage=0.0005)
    results = engine.run_ma_crossover(cleaned_df, short_window=20, long_window=50)

    initial_val = engine.initial_capital
    final_benchmark = results["Benchmark_Equity"].iloc[-1]
    final_strategy = results["Strategy_Equity"].iloc[-1]
    total_trades = int(results["Trades"].sum())

    print(f"Initial Capital:   ${initial_val:,.2f}")
    print(f"Benchmark Final:   ${final_benchmark:,.2f} ({((final_benchmark/initial_val)-1)*100:.2f}%)")
    print(f"Strategy Final:    ${final_strategy:,.2f} ({((final_strategy/initial_val)-1)*100:.2f}%)")
    print(f"Total Trades Executed: {total_trades}")

if __name__ == "__main__":
    run_backtest_test()
