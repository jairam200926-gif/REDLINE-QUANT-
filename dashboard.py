import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from datetime import datetime

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.market_data import MarketDataLoader
from app.services.data_cleaner import DataCleaner
from app.backtesting.engine import BacktestEngine
from app.backtesting.metrics import PerformanceMetrics

st.set_page_config(page_title="Quant Trading System", layout="wide")

# Technical Indicator Helpers
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist

def compute_bollinger_bands(series, window=20, num_std=2):
    sma = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    return sma + (std * num_std), sma - (std * num_std)

@st.cache_data
def get_company_name(ticker_symbol: str) -> str:
    try:
        info = yf.Ticker(ticker_symbol).info
        return info.get("longName") or info.get("shortName") or ticker_symbol.upper()
    except Exception:
        return ticker_symbol.upper()

def fetch_custom_chart_data(ticker_symbol: str, interval: str, period: str):
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period=period, interval=interval)
    if df.empty:
        raise ValueError(f"No data returned for ticker {ticker_symbol} with interval {interval} and period {period}")
    return df

POPULAR_STOCKS = {
    "US Stocks": {
        "Apple Inc. (AAPL)": "AAPL",
        "Microsoft Corporation (MSFT)": "MSFT",
        "Alphabet Inc. - Google (GOOGL)": "GOOGL",
        "Amazon.com Inc. (AMZN)": "AMZN",
        "NVIDIA Corporation (NVDA)": "NVDA",
        "Tesla Inc. (TSLA)": "TSLA",
        "Meta Platforms Inc. (META)": "META",
        "Berkshire Hathaway (BRK-B)": "BRK-B",
        "JPMorgan Chase & Co. (JPM)": "JPM",
        "Visa Inc. (V)": "V",
        "Walmart Inc. (WMT)": "WMT",
        "The Walt Disney Company (DIS)": "DIS",
        "Netflix Inc. (NFLX)": "NFLX",
        "Advanced Micro Devices (AMD)": "AMD",
        "Intel Corporation (INTC)": "INTC"
    },
    "Indian Stocks (NSE)": {
        "Reliance Industries (RELIANCE)": "RELIANCE.NS",
        "Tata Consultancy Services (TCS)": "TCS.NS",
        "Infosys Limited (INFY)": "INFY.NS",
        "HDFC Bank Ltd (HDFCBANK)": "HDFCBANK.NS",
        "ICICI Bank Ltd (ICICIBANK)": "ICICIBANK.NS",
        "Tata Motors Ltd (TATAMOTORS)": "TATAMOTORS.NS",
        "Tata Steel Ltd (TATASTEEL)": "TATASTEEL.NS",
        "State Bank of India (SBIN)": "SBIN.NS",
        "Bharti Airtel Ltd (BHARTIARTL)": "BHARTIARTL.NS",
        "ITC Limited (ITC)": "ITC.NS",
        "Larsen & Toubro Ltd (LT)": "LT.NS",
        "Hindustan Unilever (HINDUNILVR)": "HINDUNILVR.NS",
        "Wipro Limited (WIPRO)": "WIPRO.NS",
        "Maruti Suzuki India (MARUTI)": "MARUTI.NS",
        "Titan Company Ltd (TITAN)": "TITAN.NS"
    },
    "Indian Stocks (BSE)": {
        "Reliance Industries (RELIANCE)": "RELIANCE.BO",
        "Tata Consultancy Services (TCS)": "TCS.BO",
        "Infosys Limited (INFY)": "INFY.BO",
        "HDFC Bank Ltd (HDFCBANK)": "HDFCBANK.BO",
        "ICICI Bank Ltd (ICICIBANK)": "ICICIBANK.BO",
        "Tata Motors Ltd (TATAMOTORS)": "TATAMOTORS.BO",
        "Tata Steel Ltd (TATASTEEL)": "TATASTEEL.BO",
        "State Bank of India (SBIN)": "SBIN.BO",
        "Bharti Airtel Ltd (BHARTIARTL)": "BHARTIARTL.BO",
        "ITC Limited (ITC)": "ITC.BO"
    }
}

st.sidebar.markdown("> 🎯 **Market Selection**")
market = st.sidebar.selectbox("Market", ["US Stocks", "Indian Stocks (NSE)", "Indian Stocks (BSE)"])

st.sidebar.markdown("> 🔍 **Stock Search & Dropdown**")
market_options = POPULAR_STOCKS.get(market, {})
selected_stock_label = st.sidebar.selectbox(
    "Search Stock Name or Ticker",
    options=list(market_options.keys()) + ["➕ Enter Custom Ticker..."]
)

if selected_stock_label == "➕ Enter Custom Ticker...":
    raw_symbol = st.sidebar.text_input("Custom Ticker Symbol", value="AAPL").strip().upper()
    if market == "Indian Stocks (NSE)":
        ticker = raw_symbol if raw_symbol.endswith(".NS") else f"{raw_symbol}.NS"
    elif market == "Indian Stocks (BSE)":
        ticker = raw_symbol if raw_symbol.endswith(".BO") else f"{raw_symbol}.BO"
    else:
        ticker = raw_symbol
else:
    ticker = market_options[selected_stock_label]

currency = "₹" if "Indian" in market else "$"

st.sidebar.markdown("> 📊 **Strategy Parameters**")
short_window = st.sidebar.slider("Short Moving Average", min_value=5, max_value=50, value=20)
long_window = st.sidebar.slider("Long Moving Average", min_value=20, max_value=200, value=50)

st.sidebar.markdown("> 🔄 **Auto-Refresh Console**")
enable_auto_refresh = st.sidebar.checkbox("Enable Auto-Refresh", value=False)
refresh_rate_sec = st.sidebar.slider("Refresh Interval (Seconds)", min_value=5, max_value=120, value=15, step=5)

if enable_auto_refresh:
    components.html(
        f"<script>setTimeout(function(){{ window.parent.location.reload(); }}, {refresh_rate_sec * 1000});</script>",
        height=0,
    )
    st.sidebar.info(f"Auto-refreshing every {refresh_rate_sec}s")

company_name = get_company_name(ticker)
st.markdown("> # 📈 **Quantitative Algorithmic Trading System**")
st.markdown(f"> ### 🏢 **{company_name}** (`{ticker}`) | 💵 **Currency:** {currency}")
st.markdown("---")

tab1, tab2 = st.tabs(["Backtesting & Risk Analytics", "Live / Interactive Chart & Paper Trading"])

with tab1:
    st.sidebar.markdown("> 📅 **Backtest Period**")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2021-01-01"))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-12-31"))
    initial_capital = st.sidebar.number_input(f"Initial Capital ({currency})", value=10000.0 if currency == "$" else 100000.0, step=1000.0)
    
    run_button = st.button("Run Historical Backtest", type="primary")

    def run_simulation():
        loader = MarketDataLoader()
        raw_df = loader.fetch_history(ticker, str(start_date), str(end_date))
        cleaned_df, _ = DataCleaner.clean(raw_df)
        
        engine = BacktestEngine(initial_capital=initial_capital)
        results = engine.run_ma_crossover(cleaned_df, short_window=short_window, long_window=long_window)
        
        if f"SMA_{short_window}" not in results.columns:
            results[f"SMA_{short_window}"] = results["Close"].rolling(window=short_window).mean()
        if f"SMA_{long_window}" not in results.columns:
            results[f"SMA_{long_window}"] = results["Close"].rolling(window=long_window).mean()
        
        strat_metrics = PerformanceMetrics.calculate_metrics(results, "Strategy_Equity", "Strategy_Return")
        bench_metrics = PerformanceMetrics.calculate_metrics(results, "Benchmark_Equity", "Asset_Return")
        
        return results, strat_metrics, bench_metrics

    if run_button or "results" not in st.session_state:
        with st.spinner(f"Running backtest for {ticker}..."):
            try:
                results, strat_metrics, bench_metrics = run_simulation()
                st.session_state["results"] = results
                st.session_state["strat_metrics"] = strat_metrics
                st.session_state["bench_metrics"] = bench_metrics
            except Exception as e:
                st.error(f"Backtest error for '{ticker}': {e}")
                st.stop()

    results = st.session_state["results"]
    strat_metrics = st.session_state["strat_metrics"]
    bench_metrics = st.session_state["bench_metrics"]

    strat_return = strat_metrics.get("Total Return (%)", 0.0)
    bench_return = bench_metrics.get("Total Return (%)", 0.0)
    strat_sharpe = strat_metrics.get("Sharpe Ratio", 0.0)
    bench_sharpe = bench_metrics.get("Sharpe Ratio", 0.0)
    max_dd = strat_metrics.get("Max Drawdown (%)", 0.0)
    win_rate = strat_metrics.get("Win Rate (%)", 0.0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Strategy Return", f"{strat_return}%", delta=f"{round(strat_return - bench_return, 2)}% vs Bench")
    col2.metric("Sharpe Ratio", strat_sharpe, delta=f"{round(strat_sharpe - bench_sharpe, 2)}")
    col3.metric("Max Drawdown", f"{max_dd}%")
    col4.metric("Win Rate", f"{win_rate}%")

    st.markdown("---")

    short_sma_series = results.get(f"SMA_{short_window}", results["Close"].rolling(window=short_window).mean())
    long_sma_series = results.get(f"SMA_{long_window}", results["Close"].rolling(window=long_window).mean())

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3], 
        subplot_titles=(f"Equity Curves ({currency})", f"Asset Price ({currency}) & Moving Averages")
    )
    fig.add_trace(go.Scatter(x=results.index, y=results["Strategy_Equity"], mode="lines", name="Strategy Equity", line=dict(color="#00CC96", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=results.index, y=results["Benchmark_Equity"], mode="lines", name="Benchmark Equity", line=dict(color="#636EFA", width=1.5, dash="dash")), row=1, col=1)

    fig.add_trace(go.Scatter(x=results.index, y=results["Close"], mode="lines", name="Close Price", line=dict(color="#AB63FA", width=1)), row=2, col=1)
    fig.add_trace(go.Scatter(x=results.index, y=short_sma_series, mode="lines", name=f"SMA {short_window}", line=dict(color="#FFA15A")), row=2, col=1)
    fig.add_trace(go.Scatter(x=results.index, y=long_sma_series, mode="lines", name=f"SMA {long_window}", line=dict(color="#19D3F3")), row=2, col=1)

    fig.update_layout(height=600, template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("> ### 📊 **Performance Comparison**")
    st.dataframe(pd.DataFrame({"Strategy": strat_metrics, "Benchmark (Buy & Hold)": bench_metrics}), use_container_width=True)

with tab2:
    st.markdown("> ## 📉 **Live Interactive Trading Chart**")
    
    if "paper_cash" not in st.session_state:
        st.session_state["paper_cash"] = 100000.0
    if "paper_position" not in st.session_state:
        st.session_state["paper_position"] = 0
    if "buy_price" not in st.session_state:
        st.session_state["buy_price"] = 0.0
    if "trade_log" not in st.session_state:
        st.session_state["trade_log"] = []

    with st.expander("Chart Style & Indicators Controls", expanded=False):
        c_col1, c_col2, c_col3 = st.columns(3)
        chart_type = c_col1.selectbox("Chart Style", ["Candlestick", "Line", "OHLC", "Area"])
        overlays = c_col2.multiselect("Technical Overlays", ["Short SMA", "Long SMA", "Bollinger Bands"], default=["Short SMA", "Long SMA"])
        indicators = c_col3.multiselect("Sub-chart Indicators", ["Volume", "RSI", "MACD"], default=["Volume", "RSI"])

    time_range_config = {
        "1D": ("1m", "1d"),
        "5D": ("5m", "5d"),
        "1M": ("15m", "1mo"),
        "3M": ("1h", "3mo"),
        "6M": ("1d", "6mo"),
        "YTD": ("1d", "ytd"),
        "1Y": ("1d", "1y"),
        "5Y": ("1wk", "5y"),
        "ALL": ("1mo", "max")
    }

    selected_range = st.radio(
        "Time Range Selector",
        options=list(time_range_config.keys()),
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )

    interval_choice, period_choice = time_range_config[selected_range]

    try:
        df_live = fetch_custom_chart_data(ticker, interval=interval_choice, period=period_choice)
        
        latest_price = float(df_live["Close"].iloc[-1])
        prev_close = float(df_live["Close"].iloc[-2]) if len(df_live) > 1 else latest_price
        day_change = latest_price - prev_close
        day_change_pct = (day_change / prev_close) * 100
        
        df_live[f"SMA_{short_window}"] = df_live["Close"].rolling(short_window).mean()
        df_live[f"SMA_{long_window}"] = df_live["Close"].rolling(long_window).mean()
        
        latest_short = float(df_live[f"SMA_{short_window}"].iloc[-1]) if not df_live[f"SMA_{short_window}"].isnull().all() else latest_price
        latest_long = float(df_live[f"SMA_{long_window}"].iloc[-1]) if not df_live[f"SMA_{long_window}"].isnull().all() else latest_price
        sig = "BUY" if latest_short > latest_long else "SELL"
        
        l_col1, l_col2, l_col3, l_col4 = st.columns(4)
        l_col1.metric("Live Price", f"{currency}{round(latest_price, 2)}", delta=f"{round(day_change, 2)} ({round(day_change_pct, 2)}%)")
        l_col2.metric(f"SMA ({short_window})", f"{currency}{round(latest_short, 2)}")
        l_col3.metric(f"SMA ({long_window})", f"{currency}{round(latest_long, 2)}")
        sig_color = "BUY (Bullish)" if sig == "BUY" else "SELL / HOLD CASH"
        l_col4.metric("Strategy Signal", sig_color)
        
        st.markdown("---")
        
        if interval_choice in ["1d", "1wk", "1mo"]:
            x_time_labels = df_live.index.strftime("%Y-%m-%d")
        else:
            x_time_labels = df_live.index.strftime("%b %d %H:%M")
        
        num_rows = 1 + len(indicators)
        row_heights = [0.6] + [0.4 / max(1, len(indicators))] * len(indicators)
        subplot_titles = [f"{company_name} ({ticker}) - Range: {selected_range}"] + indicators
        
        fig_live = make_subplots(
            rows=num_rows, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.04, 
            row_heights=row_heights,
            subplot_titles=subplot_titles
        )
        
        if chart_type == "Candlestick":
            fig_live.add_trace(go.Candlestick(x=x_time_labels, open=df_live["Open"], high=df_live["High"], low=df_live["Low"], close=df_live["Close"], name="Price"), row=1, col=1)
        elif chart_type == "Line":
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=df_live["Close"], mode="lines", name="Close Price", line=dict(color="#AB63FA", width=1.5)), row=1, col=1)
        elif chart_type == "Area":
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=df_live["Close"], mode="lines", fill="tozeroy", name="Close Price", line=dict(color="#00CC96")), row=1, col=1)
        elif chart_type == "OHLC":
            fig_live.add_trace(go.Ohlc(x=x_time_labels, open=df_live["Open"], high=df_live["High"], low=df_live["Low"], close=df_live["Close"], name="Price"), row=1, col=1)
            
        if "Short SMA" in overlays:
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=df_live[f"SMA_{short_window}"], mode="lines", name=f"SMA {short_window}", line=dict(color="#FFA15A", width=1.5)), row=1, col=1)
        if "Long SMA" in overlays:
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=df_live[f"SMA_{long_window}"], mode="lines", name=f"SMA {long_window}", line=dict(color="#19D3F3", width=1.5)), row=1, col=1)
        if "Bollinger Bands" in overlays:
            upper_bb, lower_bb = compute_bollinger_bands(df_live["Close"])
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=upper_bb, mode="lines", name="BB Upper", line=dict(color="rgba(255,255,255,0.4)", dash="dot")), row=1, col=1)
            fig_live.add_trace(go.Scatter(x=x_time_labels, y=lower_bb, mode="lines", name="BB Lower", line=dict(color="rgba(255,255,255,0.4)", dash="dot")), row=1, col=1)

        last_x = x_time_labels[-1]
        price_badge_bg = "#00CC96" if day_change >= 0 else "#FF5252"
        
        fig_live.add_annotation(
            x=last_x, y=latest_price,
            text=f" <b>{latest_price:.2f}</b> ",
            showarrow=False,
            xanchor="left", yanchor="middle",
            bgcolor=price_badge_bg,
            font=dict(color="white", size=12),
            borderpad=4,
            row=1, col=1
        )
        
        if "Short SMA" in overlays and not np.isnan(latest_short):
            fig_live.add_annotation(
                x=last_x, y=latest_short,
                text=f" <b>SMA({short_window}): {latest_short:.2f}</b> ",
                showarrow=False,
                xanchor="left", yanchor="middle",
                bgcolor="#FFA15A",
                font=dict(color="black", size=10),
                borderpad=3,
                row=1, col=1
            )
            
        if "Long SMA" in overlays and not np.isnan(latest_long):
            fig_live.add_annotation(
                x=last_x, y=latest_long,
                text=f" <b>SMA({long_window}): {latest_long:.2f}</b> ",
                showarrow=False,
                xanchor="left", yanchor="middle",
                bgcolor="#19D3F3",
                font=dict(color="black", size=10),
                borderpad=3,
                row=1, col=1
            )

        current_row = 2
        for ind in indicators:
            if ind == "Volume":
                colors = ["#00CC96" if c >= o else "#FF6666" for c, o in zip(df_live["Close"], df_live["Open"])]
                fig_live.add_trace(go.Bar(x=x_time_labels, y=df_live["Volume"], name="Volume", marker_color=colors), row=current_row, col=1)
                current_row += 1
            elif ind == "RSI":
                rsi_vals = compute_rsi(df_live["Close"])
                fig_live.add_trace(go.Scatter(x=x_time_labels, y=rsi_vals, mode="lines", name="RSI (14)", line=dict(color="#FFD700", width=1.5)), row=current_row, col=1)
                fig_live.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
                fig_live.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
                current_row += 1
            elif ind == "MACD":
                macd, macd_sig, macd_hist = compute_macd(df_live["Close"])
                fig_live.add_trace(go.Scatter(x=x_time_labels, y=macd, mode="lines", name="MACD", line=dict(color="#00BFFF", width=1.5)), row=current_row, col=1)
                fig_live.add_trace(go.Scatter(x=x_time_labels, y=macd_sig, mode="lines", name="Signal", line=dict(color="#FF4500", width=1.5)), row=current_row, col=1)
                hist_colors = ["#00CC96" if h >= 0 else "#FF6666" for h in macd_hist]
                fig_live.add_trace(go.Bar(x=x_time_labels, y=macd_hist, name="Histogram", marker_color=hist_colors), row=current_row, col=1)
                current_row += 1

        fig_live.update_xaxes(
            type="category", 
            rangeslider_visible=False, 
            showgrid=True, 
            gridcolor="#222",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            spikedash="dash",
            spikecolor="#888",
            spikethickness=1
        )
        fig_live.update_yaxes(
            showgrid=True, 
            gridcolor="#222", 
            side="right",
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            showline=True,
            spikedash="dash",
            spikecolor="#888",
            spikethickness=1
        )
        
        fig_live.update_layout(
            height=700, 
            template="plotly_dark", 
            margin=dict(l=20, r=90, t=40, b=20), 
            showlegend=True,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig_live, use_container_width=True)
        
        st.markdown("---")
        st.markdown("> ### ⚡ **Paper Trading Execution Console**")
        
        current_holdings_val = st.session_state["paper_position"] * latest_price
        unrealized_pnl = (latest_price - st.session_state["buy_price"]) * st.session_state["paper_position"] if st.session_state["paper_position"] > 0 else 0.0
        
        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        p_col1.metric("Available Cash", f"{currency}{round(st.session_state['paper_cash'], 2)}")
        p_col2.metric("Position (Shares)", st.session_state["paper_position"])
        p_col3.metric("Holding Value", f"{currency}{round(current_holdings_val, 2)}")
        p_col4.metric("Unrealized P&L", f"{currency}{round(unrealized_pnl, 2)}", delta=f"{round(unrealized_pnl, 2)}")
        
        ex_col1, ex_col2, ex_col3 = st.columns(3)
        trade_shares = ex_col1.number_input("Order Quantity", min_value=1, value=10, step=1)
        
        if ex_col2.button(f"BUY ({trade_shares} Shares)"):
            cost = trade_shares * latest_price
            if st.session_state["paper_cash"] >= cost:
                st.session_state["paper_cash"] -= cost
                total_shares = st.session_state["paper_position"] + trade_shares
                st.session_state["buy_price"] = ((st.session_state["buy_price"] * st.session_state["paper_position"]) + cost) / total_shares
                st.session_state["paper_position"] = total_shares
                st.session_state["trade_log"].append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticker": ticker,
                    "Action": "BUY",
                    "Price": f"{currency}{round(latest_price, 2)}",
                    "Shares": trade_shares,
                    "Total Cost": f"{currency}{round(cost, 2)}"
                })
                st.success(f"Executed BUY for {trade_shares} shares at {currency}{round(latest_price, 2)}")
                st.rerun()
            else:
                st.error("Insufficient Cash Balance!")
                
        if ex_col3.button(f"SELL ({trade_shares} Shares)"):
            if st.session_state["paper_position"] >= trade_shares:
                revenue = trade_shares * latest_price
                st.session_state["paper_cash"] += revenue
                st.session_state["paper_position"] -= trade_shares
                if st.session_state["paper_position"] == 0:
                    st.session_state["buy_price"] = 0.0
                st.session_state["trade_log"].append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticker": ticker,
                    "Action": "SELL",
                    "Price": f"{currency}{round(latest_price, 2)}",
                    "Shares": trade_shares,
                    "Total Revenue": f"{currency}{round(revenue, 2)}"
                })
                st.success(f"Executed SELL for {trade_shares} shares at {currency}{round(latest_price, 2)}")
                st.rerun()
            else:
                st.error("Not enough shares held to sell!")

        st.markdown("> ### 📜 **Executed Paper Trades Log**")
        if st.session_state["trade_log"]:
            st.dataframe(pd.DataFrame(st.session_state["trade_log"]), use_container_width=True)
        else:
            st.info("No trades executed in this session yet.")

    except Exception as e:
        st.error(f"Error loading live interactive chart for '{ticker}': {e}")
