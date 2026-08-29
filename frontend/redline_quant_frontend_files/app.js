/* ============================================================
   REDLINE QUANT — MASTER FRONTEND ENGINE
   Unified State, Explicit TradingView Mapping & Multi-Market Search
   ============================================================ */

"use strict";

/* ─── Config ──────────────────────────────────────────────── */
const API_BASE = "http://localhost:8000";
const SEARCH_API = `${API_BASE}/api/market/search`;
const BACKTEST_API = `${API_BASE}/api/v1/backtest`;
const STRATEGY_LAB_API = `${API_BASE}/api/v1/strategy-lab`;

/* ─── DOM Helper ─────────────────────────────────────────── */
const $ = id => document.getElementById(id);

/* ─── Explicit TradingView Symbol Dictionary ──────────────── */
const TRADINGVIEW_SYMBOLS = {
    // Indian NSE Stocks
    ITC: "NSE:ITC",
    RELIANCE: "NSE:RELIANCE",
    TCS: "NSE:TCS",
    INFY: "NSE:INFY",
    HDFCBANK: "NSE:HDFCBANK",
    ICICIBANK: "NSE:ICICIBANK",
    SBIN: "NSE:SBIN",
    BHARTIARTL: "NSE:BHARTIARTL",
    LT: "NSE:LT",
    MARUTI: "NSE:MARUTI",
    TATAMOTORS: "NSE:TATAMOTORS",
    AXISBANK: "NSE:AXISBANK",
    KOTAKBANK: "NSE:KOTAKBANK",
    HINDUNILVR: "NSE:HINDUNILVR",

    // US NASDAQ & NYSE Stocks
    AAPL: "NASDAQ:AAPL",
    MSFT: "NASDAQ:MSFT",
    GOOGL: "NASDAQ:GOOGL",
    AMZN: "NASDAQ:AMZN",
    NVDA: "NASDAQ:NVDA",
    META: "NASDAQ:META",
    TSLA: "NASDAQ:TSLA",
    NFLX: "NASDAQ:NFLX",
    AMD: "NASDAQ:AMD",
    INTC: "NASDAQ:INTC",
    JPM: "NYSE:JPM",
    V: "NYSE:V",
    WMT: "NYSE:WMT",
    DIS: "NYSE:DIS"
};

/* ─── Curated Stock Database (Instant Offline / Local Cache) ── */
const STOCKS = [
    // Indian Stocks (NSE)
    { symbol: "ITC", name: "ITC Limited", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "ITC.NS", tradingViewSymbol: "NSE:ITC" },
    { symbol: "RELIANCE", name: "Reliance Industries Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "RELIANCE.NS", tradingViewSymbol: "NSE:RELIANCE" },
    { symbol: "TCS", name: "Tata Consultancy Services", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "TCS.NS", tradingViewSymbol: "NSE:TCS" },
    { symbol: "INFY", name: "Infosys Limited", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "INFY.NS", tradingViewSymbol: "NSE:INFY" },
    { symbol: "HDFCBANK", name: "HDFC Bank Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "HDFCBANK.NS", tradingViewSymbol: "NSE:HDFCBANK" },
    { symbol: "ICICIBANK", name: "ICICI Bank Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "ICICIBANK.NS", tradingViewSymbol: "NSE:ICICIBANK" },
    { symbol: "SBIN", name: "State Bank of India", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "SBIN.NS", tradingViewSymbol: "NSE:SBIN" },
    { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "BHARTIARTL.NS", tradingViewSymbol: "NSE:BHARTIARTL" },
    { symbol: "LT", name: "Larsen & Toubro Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "LT.NS", tradingViewSymbol: "NSE:LT" },
    { symbol: "MARUTI", name: "Maruti Suzuki India Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "MARUTI.NS", tradingViewSymbol: "NSE:MARUTI" },
    { symbol: "TATAMOTORS", name: "Tata Motors Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "TATAMOTORS.NS", tradingViewSymbol: "NSE:TATAMOTORS" },
    { symbol: "AXISBANK", name: "Axis Bank Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "AXISBANK.NS", tradingViewSymbol: "NSE:AXISBANK" },
    { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "KOTAKBANK.NS", tradingViewSymbol: "NSE:KOTAKBANK" },
    { symbol: "HINDUNILVR", name: "Hindustan Unilever Ltd.", market: "IN", exchange: "NSE", currency: "INR", backendSymbol: "HINDUNILVR.NS", tradingViewSymbol: "NSE:HINDUNILVR" },

    // US Stocks (NASDAQ & NYSE)
    { symbol: "AAPL", name: "Apple Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "AAPL", tradingViewSymbol: "NASDAQ:AAPL" },
    { symbol: "MSFT", name: "Microsoft Corporation", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "MSFT", tradingViewSymbol: "NASDAQ:MSFT" },
    { symbol: "GOOGL", name: "Alphabet Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "GOOGL", tradingViewSymbol: "NASDAQ:GOOGL" },
    { symbol: "AMZN", name: "Amazon.com Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "AMZN", tradingViewSymbol: "NASDAQ:AMZN" },
    { symbol: "NVDA", name: "NVIDIA Corporation", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "NVDA", tradingViewSymbol: "NASDAQ:NVDA" },
    { symbol: "META", name: "Meta Platforms Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "META", tradingViewSymbol: "NASDAQ:META" },
    { symbol: "TSLA", name: "Tesla Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "TSLA", tradingViewSymbol: "NASDAQ:TSLA" },
    { symbol: "NFLX", name: "Netflix Inc.", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "NFLX", tradingViewSymbol: "NASDAQ:NFLX" },
    { symbol: "AMD", name: "Advanced Micro Devices", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "AMD", tradingViewSymbol: "NASDAQ:AMD" },
    { symbol: "INTC", name: "Intel Corporation", market: "US", exchange: "NASDAQ", currency: "USD", backendSymbol: "INTC", tradingViewSymbol: "NASDAQ:INTC" },
    { symbol: "JPM", name: "JPMorgan Chase & Co.", market: "US", exchange: "NYSE", currency: "USD", backendSymbol: "JPM", tradingViewSymbol: "NYSE:JPM" },
    { symbol: "V", name: "Visa Inc.", market: "US", exchange: "NYSE", currency: "USD", backendSymbol: "V", tradingViewSymbol: "NYSE:V" },
    { symbol: "WMT", name: "Walmart Inc.", market: "US", exchange: "NYSE", currency: "USD", backendSymbol: "WMT", tradingViewSymbol: "NYSE:WMT" },
    { symbol: "DIS", name: "The Walt Disney Company", market: "US", exchange: "NYSE", currency: "USD", backendSymbol: "DIS", tradingViewSymbol: "NYSE:DIS" }
];

/* ─── Global State (Single Source of Truth) ──────────────── */
window.selectedInstrument = STOCKS[0]; // Default: ITC

/* ─── Utilities ───────────────────────────────────────────── */
function escapeHtml(str) {
    return String(str ?? "").replace(/[&<>"']/g, c => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
    })[c]);
}

function toast(msg) {
    const el = $("toast");
    if (!el) return;
    el.textContent = msg;
    el.classList.add("show");
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => el.classList.remove("show"), 3500);
}

function updateElement(id, value) {
    const el = $(id);
    if (el) el.textContent = String(value ?? "—");
}

/* ─── Resolve Clean TradingView Symbol (Explicit Map) ─────── */
function resolveTradingViewSymbol(stock) {
    if (!stock) return "NSE:ITC";
    const rawSym = String(stock.symbol || "").trim().toUpperCase().replace(/\.NS$/i, "").replace(/\.BO$/i, "");
    
    // 1. Direct match in dictionary
    if (TRADINGVIEW_SYMBOLS[rawSym]) {
        return TRADINGVIEW_SYMBOLS[rawSym];
    }
    
    // 2. Already defined clean symbol
    if (stock.tradingViewSymbol && !stock.tradingViewSymbol.includes("undefined")) {
        return String(stock.tradingViewSymbol).trim().replace(/\.NS$/i, "").replace(/\.BO$/i, "");
    }
    
    // 3. Exchange fallback
    const exchange = stock.exchange || (stock.market === "IN" ? "NSE" : "NASDAQ");
    return `${exchange}:${rawSym}`;
}

/* ─── Strict Stock Normalizer ────────────────────────────── */
function normalizeStock(stock) {
    if (!stock) return null;
    const rawSym = stock.symbol ?? stock.ticker ?? stock.code;
    if (!rawSym) return null;

    let symbol = String(rawSym).trim().toUpperCase();
    const rawExchange = String(stock.exchange ?? stock.exchDisp ?? "").toUpperCase();
    const rawMarket = String(stock.market ?? stock.country ?? "").toUpperCase();

    const isIndian = rawMarket === "IN" || rawMarket === "INDIA" ||
                     rawExchange.includes("NSE") || rawExchange.includes("BSE") ||
                     rawExchange.includes("NSI") || rawExchange.includes("BOM") ||
                     symbol.endsWith(".NS") || symbol.endsWith(".BO");

    const cleanSymbol = symbol.replace(/\.NS$/i, "").replace(/\.BO$/i, "");
    const exchange = isIndian ? (rawExchange.includes("BSE") || symbol.endsWith(".BO") ? "BSE" : "NSE") : (rawExchange.includes("NYSE") || rawExchange.includes("NY") ? "NYSE" : "NASDAQ");
    const market = isIndian ? "IN" : "US";
    const currency = stock.currency ?? (isIndian ? "INR" : "USD");
    const backendSymbol = isIndian ? `${cleanSymbol}.NS` : cleanSymbol;
    
    // Resolve clean TV Symbol
    const tradingViewSymbol = TRADINGVIEW_SYMBOLS[cleanSymbol] || `${exchange}:${cleanSymbol}`;

    return {
        symbol: cleanSymbol,
        name: stock.name ?? stock.shortname ?? stock.company_name ?? cleanSymbol,
        exchange,
        market,
        currency,
        backendSymbol,
        tradingViewSymbol
    };
}

/* ─── Central State Setter (Single Source of Truth) ──────── */
function setSelectedInstrument(stock) {
    const normalized = normalizeStock(stock);
    if (!normalized) return;

    window.selectedInstrument = normalized;

    // STEP 2 REQUIRED LOGS
    console.log("SELECTED INSTRUMENT:", window.selectedInstrument);
    console.log("TRADINGVIEW SYMBOL:", window.selectedInstrument?.tradingViewSymbol);

    // 1. Update Backtest Terminal Search Input & Active Badge
    const searchInput = $("instrumentSearch");
    if (searchInput) searchInput.value = normalized.symbol;

    const selectedBadge = $("selectedStock");
    if (selectedBadge) {
        selectedBadge.hidden = false;
        selectedBadge.textContent = `${normalized.symbol} · ${normalized.name} · ${normalized.exchange}`;
    }

    // 2. Update stock display tags across slides
    ["resultSymbol", "liveSymbol", "phoneSymbol", "marketSymbol"].forEach(id => {
        updateElement(id, normalized.symbol);
    });

    // 3. Update Market label
    updateElement("liveMarket", normalized.market === "IN" ? "NSE / India" : "US Market");

    // 4. Update Live TradingView Embed
    updateTradingView(normalized);

    // 5. Close Autocomplete Dropdown
    closeResults();

    toast(`${normalized.symbol} selected`);

    // 6. Sync Strategy Lab instrument display
    syncStrategyLabInstrument(normalized);

    // 7. Trigger backtest
    runBacktest();
}

/* ─── TradingView Embed Function ─────────────────────────── */
function updateTradingView(stock) {
    const inst = stock || window.selectedInstrument;
    if (!inst) {
        console.error("Missing TradingView symbol");
        return;
    }

    const tvSymbol = resolveTradingViewSymbol(inst);
    
    // STEP 2 & STEP 6 REQUIRED LOG
    console.log("FINAL TV SYMBOL:", tvSymbol);

    const container = $("tradingview-container");
    if (!container) {
        console.warn("tradingview-container not found in DOM.");
        return;
    }

    container.innerHTML = "";

    const iframe = document.createElement("iframe");
    iframe.id = "tradingViewFrame";
    iframe.title = "TradingView live chart";
    iframe.style.width = "100%";
    iframe.style.height = "100%";
    iframe.style.border = "none";
    iframe.style.display = "block";
    iframe.setAttribute("allowtransparency", "true");
    iframe.setAttribute("scrolling", "no");

    const params = new URLSearchParams({
        frameElementId: "tradingview-widget",
        symbol: tvSymbol,
        interval: "15",
        hidesidetoolbar: "1",
        symboledit: "0",
        saveimage: "0",
        toolbarbg: "ffffff",
        theme: "light",
        style: "1",
        timezone: "Asia/Kolkata",
        withdateranges: "1",
        hide_top_toolbar: "0",
        locale: "en"
    });

    iframe.src = `https://s.tradingview.com/widgetembed/?${params.toString()}`;
    iframe.dataset.symbol = tvSymbol;
    container.appendChild(iframe);
}

/* ─── Search / Autocomplete UI ───────────────────────────── */
function getResultsContainer() {
    return $("stockResults");
}

function closeResults() {
    const box = getResultsContainer();
    if (box) box.classList.remove("open");
}

function renderResults(stocks) {
    const box = getResultsContainer();
    if (!box) return;

    box.innerHTML = "";
    const unique = [];
    const seen = new Set();

    stocks.forEach(s => {
        const norm = normalizeStock(s);
        if (!norm) return;
        const key = `${norm.symbol}:${norm.exchange}`;
        if (!seen.has(key)) {
            seen.add(key);
            unique.push(norm);
        }
    });

    if (unique.length === 0) {
        const empty = document.createElement("div");
        empty.className = "stock-option empty";
        empty.innerHTML = `<small style="padding: 10px; display:block; color:#888;">No matching stocks found</small>`;
        box.appendChild(empty);
        box.classList.add("open");
        return;
    }

    unique.slice(0, 15).forEach((stock, idx) => {
        const row = document.createElement("div");
        row.className = `stock-option ${idx === 0 ? "active" : ""}`;
        row.setAttribute("role", "option");
        row.dataset.symbol = stock.symbol;
        row.dataset.exchange = stock.exchange;

        row.innerHTML = `
            <div class="stock-option-main">
                <strong>${escapeHtml(stock.symbol)}</strong>
                <span>${escapeHtml(stock.name)}</span>
            </div>
            <div class="stock-option-meta">
                <small>${escapeHtml(stock.exchange)}</small>
                <small style="color:var(--red); font-weight:600;">${escapeHtml(stock.market)}</small>
            </div>
        `;

        row.addEventListener("mousedown", e => {
            e.preventDefault();
            setSelectedInstrument(stock);
        });

        box.appendChild(row);
    });

    box.classList.add("open");
}

function searchLocal(query) {
    const q = String(query).trim().toUpperCase();
    if (!q) return STOCKS.slice(0, 15);

    const matches = STOCKS.filter(stock => {
        const sym = stock.symbol.toUpperCase();
        const name = stock.name.toUpperCase();
        return sym.startsWith(q) || sym.includes(q) || name.includes(q);
    });

    matches.sort((a, b) => {
        const aSym = a.symbol.toUpperCase();
        const bSym = b.symbol.toUpperCase();
        if (aSym === q) return -1;
        if (bSym === q) return 1;
        if (aSym.startsWith(q) && !bSym.startsWith(q)) return -1;
        if (!aSym.startsWith(q) && bSym.startsWith(q)) return 1;
        return 0;
    });

    return matches;
}

let searchDebounceTimer = null;
let searchAbortController = null;

async function handleSearch(query) {
    const q = String(query).trim().toUpperCase();

    // 1. Instant local results
    const local = searchLocal(q);
    renderResults(local);

    if (!q) return;

    // 2. Debounced backend query
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(async () => {
        try {
            if (searchAbortController) searchAbortController.abort();
            searchAbortController = new AbortController();

            const res = await fetch(`${SEARCH_API}?q=${encodeURIComponent(q)}`, {
                signal: searchAbortController.signal
            });

            if (!res.ok) return;
            const remote = await res.json();
            if (Array.isArray(remote) && remote.length > 0) {
                const combined = [...local, ...remote];
                renderResults(combined);
            }
        } catch (e) {
            if (e.name !== "AbortError") {
                console.warn("Backend search notice:", e);
            }
        }
    }, 200);
}

function initSearch() {
    const input = $("instrumentSearch");
    const clearBtn = $("clearInstrument");

    if (!input) return;

    input.addEventListener("focus", () => handleSearch(input.value));
    input.addEventListener("input", () => handleSearch(input.value));

    input.addEventListener("keydown", e => {
        const box = getResultsContainer();
        if (!box || !box.classList.contains("open")) return;
        const options = Array.from(box.querySelectorAll(".stock-option:not(.empty)"));
        let activeIdx = options.findIndex(el => el.classList.contains("active"));

        if (e.key === "ArrowDown") {
            e.preventDefault();
            if (activeIdx < options.length - 1) {
                options.forEach(el => el.classList.remove("active"));
                options[activeIdx + 1].classList.add("active");
                options[activeIdx + 1].scrollIntoView({ block: "nearest" });
            }
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            if (activeIdx > 0) {
                options.forEach(el => el.classList.remove("active"));
                options[activeIdx - 1].classList.add("active");
                options[activeIdx - 1].scrollIntoView({ block: "nearest" });
            }
        } else if (e.key === "Enter") {
            e.preventDefault();
            const activeEl = box.querySelector(".stock-option.active");
            if (activeEl) {
                const sym = activeEl.dataset.symbol;
                const found = STOCKS.find(s => s.symbol === sym) || { symbol: sym };
                setSelectedInstrument(found);
            } else if (options[0]) {
                const sym = options[0].dataset.symbol;
                const found = STOCKS.find(s => s.symbol === sym) || { symbol: sym };
                setSelectedInstrument(found);
            }
        } else if (e.key === "Escape") {
            closeResults();
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener("click", () => {
            input.value = "";
            input.focus();
            handleSearch("");
        });
    }

    document.addEventListener("click", e => {
        if (!e.target.closest(".search-wrap") && e.target !== input) {
            closeResults();
        }
    });
}

/* ─── Backtest Execution ─────────────────────────────────── */
async function runBacktest() {
    const status = $("terminalStatus");
    const inst = window.selectedInstrument;
    if (!inst) return;

    const fromDate = $("fromDate")?.value || "2021-01-01";
    const toDate = $("toDate")?.value || "2023-12-31";
    const fastMA = Number($("fastMA")?.value || 20);
    const slowMA = Number($("slowMA")?.value || 50);

    if (status) status.textContent = `Running ${inst.symbol} quantitative backtest...`;

    const payload = {
        symbol: inst.backendSymbol,
        start_date: fromDate,
        end_date: toDate,
        short_window: fastMA,
        long_window: slowMA,
        initial_capital: inst.market === "IN" ? 100000.0 : 10000.0
    };

    console.log("Backtest request payload:", payload);

    try {
        const res = await fetch(BACKTEST_API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        console.log("Backtest response:", data);

        updateElement("resultSymbol", data.symbol || inst.symbol);
        
        const returnVal = data.strategy_return ?? data.total_return ?? 0;
        const returnEl = $("strategyReturn");
        if (returnEl) {
            returnEl.textContent = `${returnVal >= 0 ? "+" : ""}${Number(returnVal).toFixed(2)}%`;
            returnEl.style.color = returnVal >= 0 ? "#00c853" : "var(--red)";
        }

        const winRateVal = data.win_rate ?? 0;
        updateElement("winRate", `${Number(winRateVal).toFixed(1)}%`);
        updateElement("tradeCount", data.trade_count ?? 0);

        renderEquityMiniChart(data.series?.strategy_equity);

        if (status) status.textContent = `${inst.symbol} backtest completed. Sharpe: ${Number(data.sharpe_ratio || 0).toFixed(2)}`;
        toast(`${inst.symbol} backtest complete`);
    } catch (err) {
        console.error("Backtest failed:", err);
        if (status) status.textContent = `Backtest note: ${err.message}`;
    }
}

/* ─── Mini Sparkline Chart ───────────────────────────────── */
function renderEquityMiniChart(series) {
    const container = $("equityMini");
    if (!container || !Array.isArray(series) || series.length === 0) return;

    const min = Math.min(...series);
    const max = Math.max(...series);
    const range = max - min || 1;
    const pts = series.map((val, idx) => {
        const x = (idx / (series.length - 1)) * 100;
        const y = 100 - ((val - min) / range) * 80 - 10;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");

    container.innerHTML = `
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style="width:100%;height:100%;display:block;">
            <polyline fill="none" stroke="#f32235" stroke-width="2.5" points="${pts}" />
        </svg>
    `;
}

/* ─── Scroll Reveal & Interactions ────────────────────────── */
function initReveal() {
    const elements = document.querySelectorAll(".reveal");
    if (!elements.length) return;

    if (!("IntersectionObserver" in window)) {
        elements.forEach(el => el.classList.add("visible"));
        return;
    }

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                obs.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    elements.forEach(el => observer.observe(el));
}

/* ─── Live Engine Status ──────────────────────────────────── */
async function checkEngineStatus() {
    const engineEl = document.querySelector(".engine");
    if (!engineEl) return;

    try {
        const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(4000) });
        if (res.ok) {
            engineEl.innerHTML = `<span class="live-dot" style="background:#00c853;box-shadow:0 0 10px rgba(0,200,83,0.7);"></span> LIVE ENGINE`;
        } else {
            throw new Error("offline");
        }
    } catch {
        engineEl.innerHTML = `<span class="live-dot" style="background:#f32235;box-shadow:none;"></span> ENGINE OFFLINE`;
    }
}

/* ============================================================
   STRATEGY LAB
   ============================================================ */

/* State for the last successful analysis job */
let _labJobId = null;
let _labCurrency = "USD";

/**
 * Sync the Strategy Lab instrument display card whenever a stock is selected.
 */
function syncStrategyLabInstrument(inst) {
    if (!inst) return;
    const symEl   = document.getElementById("labSymbol");
    const nameEl  = document.getElementById("labCompany");
    const exchEl  = document.getElementById("labExchange");
    if (symEl)  symEl.textContent  = inst.symbol  || "—";
    if (nameEl) nameEl.textContent = inst.name    || "—";
    if (exchEl) exchEl.textContent = inst.exchange || "—";
}

/** Format price with correct currency symbol */
function formatPrice(value, currency) {
    if (value === null || value === undefined || isNaN(value)) return "—";
    const sym = (currency === "INR") ? "₹" : "$";
    return `${sym}${Number(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

/** Format a return value with sign and % */
function formatReturn(value) {
    if (value === null || value === undefined || isNaN(value)) return "—";
    const n = Number(value);
    return `${n >= 0 ? "+" : ""}${n.toFixed(2)}%`;
}

/**
 * Animate loading steps with a delay between each.
 * Returns a cleanup function to mark remaining steps done.
 */
function animateLoadingSteps(stepIds) {
    const loadingEl = document.getElementById("labLoading");
    if (!loadingEl) return () => {};
    loadingEl.hidden = false;

    // Reset all steps
    stepIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = "lab-step";
    });

    let i = 0;
    const timers = [];

    stepIds.forEach((id, idx) => {
        const t = setTimeout(() => {
            // Mark previous step done
            if (idx > 0) {
                const prev = document.getElementById(stepIds[idx - 1]);
                if (prev) prev.classList.replace("active", "done");
            }
            const el = document.getElementById(id);
            if (el) el.classList.add("active");
        }, idx * 1400);
        timers.push(t);
    });

    return function finish() {
        timers.forEach(clearTimeout);
        stepIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) { el.className = "lab-step done"; }
        });
        if (loadingEl) loadingEl.hidden = true;
    };
}

/** Safely render all Strategy Lab result fields — no [object Object], no undefined */
function renderStrategyLabResults(data) {
    if (!data || !data.success) return;

    const currency = data.currency || "USD";
    _labCurrency = currency;

    // Show results panel, hide empty state
    const emptyEl   = document.getElementById("labEmptyState");
    const contentEl = document.getElementById("labResultsContent");
    if (emptyEl)   emptyEl.hidden   = true;
    if (contentEl) contentEl.hidden = false;

    const s = data.summary || {};

    // Header
    document.getElementById("resSymbol").textContent  = String(data.symbol  || "—");
    document.getElementById("resCompany").textContent = String(data.company || "—");

    // Overall return
    const retEl = document.getElementById("resReturn");
    const retVal = s.overallReturn;
    if (retEl) {
        retEl.textContent = formatReturn(retVal);
        retEl.style.color = (retVal !== null && Number(retVal) >= 0) ? "#00a344" : "var(--red)";
    }

    // Prices
    document.getElementById("resHigh").textContent = formatPrice(s.highestPrice, currency);
    document.getElementById("resLow").textContent  = formatPrice(s.lowestPrice,  currency);

    // Best / Worst Day
    const bd = data.bestDay  || {};
    const wd = data.worstDay || {};
    document.getElementById("resBestDayReturn").textContent  = formatReturn(bd.return);
    document.getElementById("resBestDayDate").textContent    = String(bd.date || "—");
    document.getElementById("resWorstDayReturn").textContent = formatReturn(wd.return);
    document.getElementById("resWorstDayDate").textContent   = String(wd.date || "—");

    // Best / Worst Week
    const bw = data.bestWeek  || {};
    const ww = data.worstWeek || {};
    document.getElementById("resBestWeekReturn").textContent  = formatReturn(bw.return);
    document.getElementById("resBestWeekDate").textContent    = String(bw.date || "—");
    document.getElementById("resWorstWeekReturn").textContent = formatReturn(ww.return);
    document.getElementById("resWorstWeekDate").textContent   = String(ww.date || "—");

    // SMA values
    document.getElementById("resSMA20").textContent = formatPrice(s.lastSMA20, currency);
    document.getElementById("resSMA50").textContent = formatPrice(s.lastSMA50, currency);
}

/**
 * Trigger a download by navigating to the backend file endpoint.
 */
function downloadLabFile(jobId, type) {
    if (!jobId) {
        toast("Run an analysis first.");
        return;
    }
    const url = `${API_BASE}/api/v1/strategy-lab/download/${encodeURIComponent(jobId)}/${type}`;
    const a = document.createElement("a");
    a.href = url;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

/** Main Strategy Lab runner */
async function runStrategyLab() {
    const inst = window.selectedInstrument;
    if (!inst || !inst.symbol) {
        toast("Select an instrument first.");
        return;
    }

    const btn    = document.getElementById("runStrategyLab");
    const status = document.getElementById("labStatus");

    // Disable button while running
    if (btn) { btn.disabled = true; btn.style.opacity = "0.6"; }
    if (status) status.textContent = `Analyzing ${inst.symbol} — 60-day intraday data (15-min)…`;

    // Show animated loading steps
    const finishLoading = animateLoadingSteps(["step1", "step2", "step3", "step4"]);

    const payload = {
        symbol:       inst.symbol,
        backendSymbol: inst.backendSymbol,
        company:      inst.name     || inst.symbol,
        currency:     inst.currency || (inst.market === "IN" ? "INR" : "USD"),
    };

    console.log("Strategy Lab request:", payload);

    try {
        const res = await fetch(STRATEGY_LAB_API, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();
        console.log("Strategy Lab response:", data);

        // Store job ID for download buttons
        _labJobId = data.job_id || null;

        finishLoading();

        renderStrategyLabResults(data);

        const pts = data.data_points || 0;
        if (status) status.textContent = `${inst.symbol} — ${pts} data points analysed. Download ready.`;
        toast(`${inst.symbol} analysis complete.`);

    } catch (err) {
        finishLoading();
        console.error("Strategy Lab failed:", err);
        const msg = err.message || "Analysis failed.";

        if (msg.toLowerCase().includes("no") && msg.toLowerCase().includes("data")) {
            if (status) status.textContent = "No market data found for this instrument.";
            toast("No market data found.");
        } else if (msg.toLowerCase().includes("invalid") || msg.toLowerCase().includes("unsupported")) {
            if (status) status.textContent = "Invalid or unsupported instrument.";
            toast("Invalid instrument.");
        } else {
            if (status) status.textContent = `Analysis failed. Please try again.`;
            toast("Analysis failed. Check console.");
        }
    } finally {
        if (btn) { btn.disabled = false; btn.style.opacity = ""; }
    }
}

/* ============================================================
   BEGINNER GUIDE RESEARCH INTERACTIVITY
   ============================================================ */
function initBeginnerGuide() {
    // 1. Concept Card Accordions (Learn More -> Show Less)
    const learnMoreButtons = document.querySelectorAll(".learn-more-btn");
    learnMoreButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const card = btn.closest(".concept-card");
            if (!card) return;
            const detail = card.querySelector(".concept-detail");
            if (!detail) return;

            const isExpanded = btn.getAttribute("aria-expanded") === "true";
            if (isExpanded) {
                detail.hidden = true;
                btn.setAttribute("aria-expanded", "false");
                btn.innerHTML = `Learn more <span>&rarr;</span>`;
            } else {
                detail.hidden = false;
                btn.setAttribute("aria-expanded", "true");
                btn.innerHTML = `Show less <span>&uarr;</span>`;
            }
        });
    });

    // 2. Learning Path Track Highlighting
    const pathCards = document.querySelectorAll(".path-card");
    const guideBlocks = document.querySelectorAll(".guide-block");

    pathCards.forEach(card => {
        card.addEventListener("click", () => {
            pathCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
        });
    });

    // Active track scroll observer
    if ("IntersectionObserver" in window && guideBlocks.length) {
        const topicObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.id;
                    pathCards.forEach(card => {
                        const targetHref = card.getAttribute("href");
                        if (targetHref === `#${id}`) {
                            pathCards.forEach(c => c.classList.remove("active"));
                            card.classList.add("active");
                        }
                    });
                }
            });
        }, { rootMargin: "-20% 0px -60% 0px" });

        guideBlocks.forEach(block => topicObserver.observe(block));
    }
}

/* ─── Init on DOM Load ────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
    console.log("REDLINE QUANT initializing...");

    initSearch();
    initReveal();
    initBeginnerGuide();

    // Default to ITC
    setSelectedInstrument(STOCKS[0]);

    // Backtest Terminal button
    document.getElementById("runBacktest")?.addEventListener("click", e => {
        e.preventDefault();
        runBacktest();
    });

    // Strategy Lab — Run Analysis button
    document.getElementById("runStrategyLab")?.addEventListener("click", e => {
        e.preventDefault();
        runStrategyLab();
    });

    // Strategy Lab — Download CSV
    document.getElementById("downloadCsv")?.addEventListener("click", () => {
        downloadLabFile(_labJobId, "csv");
    });

    // Strategy Lab — Download Excel
    document.getElementById("downloadExcel")?.addEventListener("click", () => {
        downloadLabFile(_labJobId, "excel");
    });

    // Engine health check
    checkEngineStatus();
    setInterval(checkEngineStatus, 30000);

    console.log("REDLINE QUANT ready.");
});

// Global API
window.RedlineQuant = {
    getSelectedInstrument: () => window.selectedInstrument,
    setSelectedInstrument,
    runBacktest,
    runStrategyLab,
    updateTradingView,
    initBeginnerGuide,
};