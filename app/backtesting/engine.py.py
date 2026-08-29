import pandas as pd
import numpy as np

class BacktestEngine:
    """
    Simulates historical trading strategies and computes strategy equity curves.
    """

    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001, slippage: float = 0.0005):
        """
        Args:
            initial_capital: Starting portfolio value in cash (e.g., $10,000).
            commission: Broker fee percentage per trade (0.001 = 0.1%).
            slippage: Estimated price impact penalty (0.0005 = 0.05%).
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run_ma_crossover(self, df: pd.DataFrame, short_window: int = 20, long_window: int = 50, price_col: str = "Close") -> pd.DataFrame:
        """
        Moving Average Crossover Strategy:
        - Buy (Signal = 1) when Short SMA > Long SMA.
        - Exit to Cash (Signal = 0) when Short SMA <= Long SMA.
        """
        data = df.copy()

        # 1. Calculate Moving Averages if missing
        if f"SMA_{short_window}" not in data.columns:
            data[f"SMA_{short_window}"] = data[price_col].rolling(window=short_window).mean()
        if f"SMA_{long_window}" not in data.columns:
            data[f"SMA_{long_window}"] = data[price_col].rolling(window=long_window).mean()

        # 2. Generate Raw Signals
        # 1 when short MA > long MA, else 0
        data["Raw_Signal"] = np.where(data[f"SMA_{short_window}"] > data[f"SMA_{long_window}"], 1, 0)

        # 3. Shift Signal by 1 period to prevent Lookahead Bias
        # Today's close generates a signal executed at tomorrow's close
        data["Position"] = data["Raw_Signal"].shift(1).fillna(0)

        # 4. Calculate Trades (1 when position changes, else 0)
        data["Trades"] = data["Position"].diff().abs().fillna(0)

        # 5. Calculate Asset Returns
        data["Asset_Return"] = data[price_col].pct_change().fillna(0)

        # 6. Apply Transaction Costs and Slippage on trade entry/exit
        total_friction = self.commission + self.slippage
        friction_penalty = data["Trades"] * total_friction

        # 7. Calculate Strategy Return
        data["Strategy_Return"] = (data["Position"] * data["Asset_Return"]) - friction_penalty

        # 8. Calculate Portfolio Equity Curves
        data["Benchmark_Equity"] = self.initial_capital * (1 + data["Asset_Return"]).cumprod()
        data["Strategy_Equity"] = self.initial_capital * (1 + data["Strategy_Return"]).cumprod()

        return data