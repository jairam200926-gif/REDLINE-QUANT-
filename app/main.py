import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np

# Ensure parent directory is in sys.path for relative imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from api.market import router as market_router
from api.schemas import BacktestRequest
from services.market_data import MarketDataLoader
from services.intraday_analyzer import IntradayAnalyzer
from analysis.strategy_lab import run_strategy_analysis, _DATA_DIR
from backtesting.engine import BacktestEngine
from backtesting.metrics import PerformanceMetrics

app = FastAPI(
    title="Redline Quant Trading System API",
    description="Backend service providing real-time market data, indicators, backtesting, and strategy execution.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(market_router)

@app.get("/")
def root():
    return {"status": "online", "message": "Quant Trading Backend API is running"}


# ============================================================
# STRATEGY LAB — full 60-day intraday analysis
# ============================================================

class StrategyLabRequest(BaseModel):
    symbol: str = "AAPL"          # Display ticker, e.g. "ITC"
    backendSymbol: str = ""        # yfinance ticker, e.g. "ITC.NS"
    company: str = ""              # Company name, e.g. "ITC Limited"
    currency: str = "USD"          # "INR" or "USD"

@app.post("/api/v1/strategy-lab")
def run_strategy_lab(req: StrategyLabRequest):
    try:
        # Determine the correct yfinance symbol
        backend_sym = req.backendSymbol.strip() if req.backendSymbol.strip() else req.symbol.strip()
        if not backend_sym:
            raise HTTPException(status_code=422, detail="No stock symbol provided.")

        result = run_strategy_analysis(
            backend_symbol=backend_sym,
            company_name=req.company,
            currency=req.currency,
        )

        # Strip internal filesystem paths before returning to frontend
        result.pop("_csv_path", None)
        result.pop("_excel_path", None)

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================
# STRATEGY LAB DOWNLOAD ENDPOINTS
# ============================================================

@app.get("/api/v1/strategy-lab/download/{job_id}/csv")
def download_csv(job_id: str):
    """Return the generated 15-minute CSV as a file download."""
    # Sanitize job_id to prevent path traversal
    safe_id = job_id.replace("..", "").replace("/", "").replace("\\", "")
    job_path = _DATA_DIR / safe_id

    # Find the CSV file in the job directory
    csv_files = list(job_path.glob("*_15m.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail="CSV file not found. Run the analysis first.")

    csv_file = csv_files[0]
    return FileResponse(
        path=str(csv_file),
        media_type="text/csv",
        filename=csv_file.name,
        headers={"Content-Disposition": f'attachment; filename="{csv_file.name}"'},
    )


@app.get("/api/v1/strategy-lab/download/{job_id}/excel")
def download_excel(job_id: str):
    """Return the generated Excel analysis as a file download."""
    safe_id = job_id.replace("..", "").replace("/", "").replace("\\", "")
    job_path = _DATA_DIR / safe_id

    excel_files = list(job_path.glob("*_15m_Analysis.xlsx"))
    if not excel_files:
        raise HTTPException(status_code=404, detail="Excel file not found. Run the analysis first.")

    excel_file = excel_files[0]
    return FileResponse(
        path=str(excel_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=excel_file.name,
        headers={"Content-Disposition": f'attachment; filename="{excel_file.name}"'},
    )


# ============================================================
# BACKTEST TERMINAL (unchanged)
# ============================================================

@app.post("/api/v1/backtest")
def run_backtest(req: BacktestRequest):
    try:
        loader = MarketDataLoader()
        symbol = req.symbol.strip().upper()
        # Resolve Indian suffix if not specified
        if not symbol.endswith(".NS") and not symbol.endswith(".BO") and symbol in ("ITC", "RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN", "ICICIBANK", "BHARTIARTL", "LT", "MARUTI", "TATAMOTORS", "AXISBANK", "KOTAKBANK", "HINDUNILVR"):
            symbol = f"{symbol}.NS"

        df = loader.fetch_history(symbol, req.start_date, req.end_date)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No price data available for {symbol}")

        engine = BacktestEngine(
            initial_capital=req.initial_capital,
            commission=req.commission,
            slippage=req.slippage
        )

        result_df = engine.run_ma_crossover(df, short_window=req.short_window, long_window=req.long_window)
        metrics = PerformanceMetrics.calculate_metrics(result_df)

        currency = "INR" if symbol.endswith((".NS", ".BO")) else "USD"

        # Calculate benchmark return
        benchmark_total_return = round(float(((result_df["Close"].iloc[-1] / result_df["Close"].iloc[0]) - 1) * 100), 2)
        strat_total_return = metrics.get("Total Return (%)", 0.0)

        # Number of trades
        trade_count = int(result_df["Trades"].sum()) if "Trades" in result_df.columns else 0

        # Win rate
        win_rate = metrics.get("Win Rate (%)", 0.0)

        dates = [d.strftime("%Y-%m-%d") for d in result_df.index]

        return {
            "symbol": req.symbol.upper().replace(".NS", "").replace(".BO", ""),
            "backendSymbol": symbol,
            "currency": currency,
            "strategy_return": strat_total_return,
            "total_return": strat_total_return,
            "benchmark_return": benchmark_total_return,
            "sharpe_ratio": metrics.get("Sharpe Ratio", 0.0),
            "max_drawdown": metrics.get("Max Drawdown (%)", 0.0),
            "win_rate": win_rate,
            "trade_count": trade_count,
            "data_points": len(result_df),
            "final_equity": round(float(result_df["Strategy_Equity"].iloc[-1]), 2),
            "series": {
                "dates": dates,
                "close": [round(float(v), 2) for v in result_df["Close"]],
                "strategy_equity": [round(float(v), 2) for v in result_df["Strategy_Equity"]],
                "benchmark_equity": [round(float(v), 2) for v in result_df["Benchmark_Equity"]]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)