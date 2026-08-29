from pydantic import BaseModel

class BacktestRequest(BaseModel):
    symbol: str = "AAPL"
    start_date: str = "2021-01-01"
    end_date: str = "2023-12-31"
    initial_capital: float = 10000.0
    short_window: int = 20
    long_window: int = 50
    commission: float = 0.001
    slippage: float = 0.0005
