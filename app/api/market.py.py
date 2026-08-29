from fastapi import APIRouter, HTTPException
from services.market_data import MarketDataLoader

router = APIRouter(prefix="/api/market", tags=["Market Data"])

@router.get("/history/{ticker}")
def fetch_history(ticker: str, start: str = "2021-01-01", end: str = "2023-12-31"):
    try:
        loader = MarketDataLoader()
        df = loader.fetch_history(ticker, start, end)
        return df.reset_index().to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))