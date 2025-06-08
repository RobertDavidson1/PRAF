Here’s your original component breakdown, fully rewritten to incorporate the best‐practice improvements we discussed:

---
### 1. Purpose

- **Monthly cron job** (runs 05:00 UTC on the 1st) to:
    1. Fetch the list of tickers for each exchange
    2. Normalize & upsert into the master metadata DB
    3. Emit a Parquet snapshot of the parsed tickers
    4. Log structured JSON about each stage
- **Master Ticker Table**: `data/db/meta.sqlite`
- **Parsed Snapshots**: `data/artifacts/staging/<EXCHANGE>_<YYYYMMDD>.parquet`
---
### 2. High-Level Flow

```text
cron → run_scraper.sh
        │
        └─ python -m scraper.cli run
              │
              ├─ Load config (YAML + .env via pydantic)
              ├─ init_db()  # create tables if missing via SQLAlchemy
              ├─ for each exchange:
              │     ├─ fetch raw (requests or Selenium via driver.py)
              │     ├─ [optional] save raw HTML/JSON
              │     ├─ parse → pandas.DataFrame
              │     ├─ save staging Parquet (adds scrape_date metadata)
              │     └─ upsert batch into meta.sqlite (ticker, status, first_seen, last_seen)
              └─ exit with code:
                    • 0 = all OK  
                    • 10 = retryable error  
                    • 20 = fatal error  
                    • 1 = unexpected
```

---
### 3. Directory Layout
```text
repo-root/
│
├── config/
│   ├── exchanges.yaml         # list of {name, url, optional click_sequence}
│   └── cron/
│       ├── run_scraper        # cron @05:00 UTC on the 1st → run_scraper.sh
│       └── janitor_artifacts  # cron @02:00 UTC daily → delete >365 d old files
│
├── data/
│   ├── db/
│   │   └── meta.sqlite        # SQLite metadata DB  
│   ├── artifacts/
│   │   └── staging/           # immutable Parquet snapshots  
│   │       └── LSE_20250701.parquet  
│   ├── logs/
│   │   └── scraper_2025-07-01.jsonl  
│   └── backups/
│       └── 2025-07-01_meta.sqlite.gz  
│
├── scraper/
│   ├── __init__.py
│   ├── cli.py                 # click/argparse entrypoint
│   ├── config.py              # pydantic settings + YAML loader
│   ├── db.py                  # SQLAlchemy engine + upsert helper
│   ├── driver.py              # Selenium/session wrapper
│   ├── fetchers/              # per-exchange fetch logic
│   └── parsers/               # per-exchange normalization
│
├── tests/                     # pytest suite
│   ├── test_fetchers.py
│   ├── test_parsers.py
│   └── test_db.py
│
└── .env                       # META_DB_URL, STAGING_DIR, LOG_LEVEL, etc.
```

---

### 4. Logging

Structured JSON (via `structlog` or `logging`+JSON formatter), e.g.:

```jsonc
{
  "ts":       "2025-07-01T05:00:00Z",
  "level":    "INFO",
  "exchange": "LSE",
  "stage":    "parse",
  "count":    3241,
  "ok":       true,
  "msg":      "Parsed rows successfully"
}
```
Fields:
- `ts` (ISO 8601 UTC)
- `exchange`
- `stage` (`fetch`, `parse`, `upsert`, `snapshot`, `complete`)
- `count` or `error`    
- `ok` (bool) 
---
### 5. exchanges.yaml

```yaml
- name: LSE
  url:  https://example.com/lse-tickers
  click_sequence:
    - "button#1"
    - "button#2"

- name: NASDAQ
  url:  https://example.com/nasdaq-list"
  # click_sequence: []
```

---

### 6. Cron Snippets
**run_scraper** (`config/cron/run_scraper`):
```cron
5 0 1 * * cd /path/to/repo && ./run_scraper.sh
```
**janitor_artifacts** (delete >365 days old):
```cron
0 2 * * * cd /path/to/repo && ./config/cron/janitor_artifacts
```
---
### 7. Retention & Cleanup
- **Back up** `meta.sqlite` monthly (pre-scrape) to `data/backups/2025-XX-01_meta.sqlite.gz`.
- **Prune** staging Parquets and backups older than 365 days in `janitor_artifacts`.
    
---
### 8. Testing & CI
- **Unit tests**
    - Fetchers: mock HTTP/Selenium
    - Parsers: validate DataFrame schema
    - DB: `sqlite:///:memory:` for init & upsert
- **CI**: run `pytest`, `flake8`, `mypy` on each push.

---

