import numpy as np
import pandas as pd
from typing import Dict, Any

class PerformanceMetrics:
    """
    Computes quantitative strategy performance and risk-adjusted return metrics.
    """
    @staticmethod
    def calculate_metrics(df: pd.DataFrame, equity_col: str = "Strategy_Equity", return_col: str = "Strategy_Return", risk_free_rate: float = 0.02) -> Dict[str, Any]:
        equity = df[equity_col].dropna()
        returns = df[return_col].dropna()

        if len(equity) < 2:
            return {"status": "ERROR", "message": "Insufficient data"}

        # Total Return & CAGR
        total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
        num_years = max((equity.index[-1] - equity.index[0]).days / 365.25, 0.001)
        cagr = ((1 + total_return) ** (1 / num_years)) - 1

        # Volatility (Annualized)
        ann_volatility = returns.std() * np.sqrt(252)

        # Sharpe Ratio
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = returns - daily_rf
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0.0

        # Sortino Ratio
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (cagr - risk_free_rate) / downside_std if downside_std > 0 else 0.0

        # Maximum Drawdown
        cum_max = equity.cummax()
        drawdowns = (equity - cum_max) / cum_max
        max_drawdown = drawdowns.min()

        # Win Rate & Trade Count
        active_returns = returns[df["Trades"] > 0] if "Trades" in df.columns else returns[returns != 0]
        winning_trades = active_returns[active_returns > 0]
        losing_trades = active_returns[active_returns < 0]
        total_active_trades = len(winning_trades) + len(losing_trades)
        
        win_rate = (len(winning_trades) / total_active_trades) if total_active_trades > 0 else 0.0

        # Profit Factor
        gross_profit = winning_trades.sum()
        gross_loss = abs(losing_trades.sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan

        return {
            "Total Return (%)": round(total_return * 100, 2),
            "CAGR (%)": round(cagr * 100, 2),
            "Annual Volatility (%)": round(ann_volatility * 100, 2),
            "Sharpe Ratio": round(sharpe_ratio, 2),
            "Sortino Ratio": round(sortino_ratio, 2),
            "Max Drawdown (%)": round(max_drawdown * 100, 2),
            "Win Rate (%)": round(win_rate * 100, 2),
            "Profit Factor": round(profit_factor, 2) if not np.isnan(profit_factor) else "N/A"
        }
