# Stock-Data Pipeline – Project Outline  
*(work-in-progress master context for the o4-mini-high model)*  

> **Purpose** – Capture a concise yet comprehensive roadmap of the end-to-end system:  
> • Monthly exchange scraping ➜ ticker universe  
> • Nightly Yahoo Finance fetch ➜ OHLCV lake  
> • Daily QA ➜ Web dashboard & Telegram alerts  
> • Minimal tech stack but clear upgrade path  

---

## 1 · High-Level Architecture & Workflow
- **Data-flow**  
  1. **Monthly Scraper (00:05 UTC, 1st)** – pulls latest ticker lists from LSE, NASDAQ, NYSE, NYSE Arca, Euronext, etc.  
     - `requests` + `BeautifulSoup` for static pages  
     - **`selenium`** (headless Chrome) for pages requiring clicks  
     - Scraper process bound to NordVPN via `pynordvpn`; one VPN hop per exchange  
  2. **Relational DB (meta.db)** – UPSERTS ticker metadata (`tickers` table)  
  3. **Nightly Fetcher (01:00 UTC)** – downloads incremental OHLCV via **`yfinance`**  
     - 100 symbols per batch, 6 threads  
     - **VPN rotates every X = 400 tickers** (≈ 4 batches)  
  4. **Parquet Lake** – `/data/historical/symbol=<SYM>/year=<YYYY>/`  
  5. **QA Runner (01:45 UTC)** – computes lag, missing dates, NaNs, zero-volume, price spikes  
     - Records results in `qa_failures` & `qa_summary` tables  
  6. **Alert Dispatcher (02:00 UTC)** – Telegram via `python-telegram-bot` if thresholds breached  
  7. **FastAPI + React/Tailwind Web App** – serves dashboards & JSON APIs

- **Scheduling (cron examples)**  
  ```cron
  5 0 1 * *  python scripts/ingest_tickers.py
  0 1 * * *  python scripts/fetch_history.py
 45 1 * * *  python qa/qc_run.py
  0 2 * * *  python scripts/send_alerts.py
````

---

## 2 · Data Acquisition Best Practices

* **Scraper**

  * Retry/back-off `[2, 8, 30]s` for HTTP ≥ 500
  * Hash raw HTML to detect DOM drift; raise `structure_error` if col count changes > 10 %
  * Mark stale symbols `status='delisted'` but retain rows
* **VPN Strategy**

  * `pynordvpn.connect()` in each fetch worker (process-scoped)
  * Rotate exit node every **400 tickers** (≈ 12 MB traffic/IP)
  * On VPN failure ➜ drop to direct IP with half batch size & yellow alert
* **yfinance**

  * Exponential back-off on 429 `[10, 30, 120]s`
  * Cache raw CSV 24 h for replay
  * After 3 consecutive failures, symbol goes to DLQ

---

## 3 · Data Storage & Structure

| Layer    | Engine (MVP)           | Upgrade Path             | Notes                          |
| -------- | ---------------------- | ------------------------ | ------------------------------ |
| Metadata | **SQLite** (`meta.db`) | PostgreSQL / TimescaleDB | single-file, WAL vacuum weekly |
| OHLCV    | **Parquet**            | S3 / MinIO               | partition: symbol / year       |
| QA & DLQ | same DB                | —                        | `qa_failures`, `fetch_errors`  |

### Key Tables

| tickers                  | fetch\_errors  | qa\_failures |
| ------------------------ | -------------- | ------------ |
| symbol PK                | symbol PK      | id PK        |
| exchange\_code           | last\_attempt  | symbol       |
| status                   | error\_msg     | date         |
| first\_seen / last\_seen | failure\_count | check\_name  |
| last\_fetched\_date      |                | details JSON |

---

## 4 · Data Labelling & Metadata

* **Ticker fields:** symbol, exchange, ISIN (if parseable), currency, first\_seen, last\_seen, status
* **Price fields (Parquet):** date, open, high, low, close, adj\_close, volume, corporate\_action\_flag
* **Operational metadata:** last\_fetched\_date, consecutive\_failures, fetch\_latency\_ms, vpn\_exit\_ip

---

## 5 · Data Quality & Monitoring

### Daily Metrics (Global Summary Bar)

| Metric                         | Flag rule             | Panel link        |
| ------------------------------ | --------------------- | ----------------- |
| Total active                   | —                     | Universe Health   |
| New tickers 30d                | >100 yellow           | Universe Health   |
| Delisted 30d                   | >100 orange           | Universe Health   |
| Lag > 2 trading days           | >2 % yellow, >5 % red | Data Timeliness   |
| Tickers with missing dates 30d | >1 % yellow, >5 % red | Data Completeness |
| Fetch errors last night        | >50 red               | Fetch Errors      |
| Unexplained price jumps 7d     | >10 yellow, >25 red   | Price Quality     |

* **Anomaly checks:** lag, missing dates, NaNs, zero volume on open day, |ΔP| > 75 % w/o split, correlation drift

---

## 6 · Web App Design & Daily Metrics

* **Backend:** FastAPI, SQLModel, simple CORS JSON APIs
* **Frontend:** React (↑Vite) + Tailwind; charts via **Chart.js**; tables via **TanStack Table**
* **Pages:** Dashboard (summary + panels), Symbol drill-down, Fetch error list, QA trend page

---

## 7 · Best Practices & Tooling

* **Structured logging:** `loguru` ➜ JSON to stdout; one file per job rotated daily
* **Secrets:** `.env` + `python-decouple`; NordVPN creds via env only
* **CI:** GitHub Actions – lint, pytest, black, small E2E on dummy tickers

---

## 8 · Scheduling & Orchestration Details

* Pure cron; dependency enforced by exit code + DB flags (`scrape_status`)
* **Backfill:** if nightly fetch misses >1 day, fetcher auto-extends start\_date backwards until gap closed

---

## 9 · Logging, Alerting & Error Handling

* **Error schema:** `{code:str, msg:str, stack:str, context:JSON}`
* **Retention:** 14 days logs local, 90 days compressed archive
* **Alerts:** Telegram bot; severity emoji (🚩 red, ⚠ yellow)

---

## 10 · Documentation

```
docs/
├── architecture.md
├── data_model.md
├── monitoring.md
├── runbooks/
│   ├── scraper_failure.md
│   └── fetcher_backfill.md
└── diagrams/ (draw.io .svg)
```

* README top-level quick-start; ADRs for major tech choices

---

## 11 · Testing & Validation

* **Unit tests:** scraper parser, yfinance wrapper, QA logic
* **Integration:** run full pipeline on 10 mock tickers (local HTML fixtures, yfinance monkey-patch)
---

