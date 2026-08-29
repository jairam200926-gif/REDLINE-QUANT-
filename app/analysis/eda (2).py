import pandas as pd
import numpy as np

class MarketAnalyzer:
    @staticmethod
    def calculate_returns(df: pd.DataFrame, price_col: str = "Close") -> pd.DataFrame:
        result_df = df.copy()
        result_df["Daily_Return"] = result_df[price_col].pct_change()
        result_df["Cumulative_Return"] = (1 + result_df["Daily_Return"].fillna(0)).cumprod()
        return result_df

    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20, return_col: str = "Daily_Return") -> pd.DataFrame:
        result_df = df.copy()
        if return_col not in result_df.columns:
            raise ValueError(f"Column '{return_col}' not found.")
        result_df[f"Volatility_{window}d"] = result_df[return_col].rolling(window=window).std() * np.sqrt(252)
        return result_df