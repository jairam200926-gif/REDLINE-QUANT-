import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

def test_api_endpoints():
    client = TestClient(app)
    
    print("--- Testing Health Check Endpoint ---")
    health_res = client.get("/")
    print(f"Status Code: {health_res.status_code}")
    print(f"Response: {health_res.json()}")

    print("\n--- Testing /api/v1/backtest Endpoint ---")
    payload = {
        "symbol": "AAPL",
        "start_date": "2021-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 10000.0,
        "short_window": 20,
        "long_window": 50
    }
    res = client.post("/api/v1/backtest", json=payload)
    print(f"Status Code: {res.status_code}")
    print("Response JSON:")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test_api_endpoints()
