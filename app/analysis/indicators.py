import pandas as pd

class TechnicalIndicators:
    @staticmethod
    def add_sma(df: pd.DataFrame, window: int = 20, price_col: str = "Close") -> pd.DataFrame:
        result_df = df.copy()
        result_df[f"SMA_{window}"] = result_df[price_col].rolling(window=window).mean()
        return result_df

    @staticmethod
    def add_ema(df: pd.DataFrame, window: int = 20, price_col: str = "Close") -> pd.DataFrame:
        result_df = df.copy()
        result_df[f"EMA_{window}"] = result_df[price_col].ewm(span=window, adjust=False).mean()
        return result_df

    @staticmethod
    def add_rsi(df: pd.DataFrame, window: int = 14, price_col: str = "Close") -> pd.DataFrame:
        result_df = df.copy()
        delta = result_df[price_col].diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.ewm(com=window-1, adjust=False).mean()
        avg_loss = loss.ewm(com=window-1, adjust=False).mean()
        rs = avg_gain / avg_loss
        result_df[f"RSI_{window}"] = 100 - (100 / (1 + rs))
        return result_df

    @staticmethod
    def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, price_col: str = "Close") -> pd.DataFrame:
        result_df = df.copy()
        ema_fast = result_df[price_col].ewm(span=fast, adjust=False).mean()
        ema_slow = result_df[price_col].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        result_df["MACD"] = macd_line
        result_df["MACD_Signal"] = signal_line
        result_df["MACD_Histogram"] = macd_line - signal_line
        return result_df
