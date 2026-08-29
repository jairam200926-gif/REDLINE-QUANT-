import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run_ma_crossover(self, df: pd.DataFrame, short_window: int = 20, long_window: int = 50, price_col: str = "Close") -> pd.DataFrame:
        data = df.copy()

        if f"SMA_{short_window}" not in data.columns:
            data[f"SMA_{short_window}"] = data[price_col].rolling(window=short_window).mean()
        if f"SMA_{long_window}" not in data.columns:
            data[f"SMA_{long_window}"] = data[price_col].rolling(window=long_window).mean()

        # Generate signals (1 = Buy, 0 = Hold/Cash)
        data["Raw_Signal"] = np.where(data[f"SMA_{short_window}"] > data[f"SMA_{long_window}"], 1, 0)
        
        # Shift signals by 1 to prevent lookahead bias
        data["Position"] = data["Raw_Signal"].shift(1).fillna(0)
        data["Trades"] = data["Position"].diff().abs().fillna(0)
        data["Asset_Return"] = data[price_col].pct_change().fillna(0)

        # Apply fees and slippage on trades
        total_friction = self.commission + self.slippage
        friction_penalty = data["Trades"] * total_friction

        data["Strategy_Return"] = (data["Position"] * data["Asset_Return"]) - friction_penalty
        data["Benchmark_Equity"] = self.initial_capital * (1 + data["Asset_Return"]).cumprod()
        data["Strategy_Equity"] = self.initial_capital * (1 + data["Strategy_Return"]).cumprod()

        return data
