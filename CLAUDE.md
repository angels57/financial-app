# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Streamlit financial dashboard ("Financial Stre") that lets users enter a stock ticker and view financial summaries, charts, valuation metrics, technical analysis, and news. Data comes from yfinance. The UI is in Spanish.

## Commands

```bash
# Install dependencies
uv sync

# Run the app (Streamlit)
uv run streamlit run app/main.py

# Lint and format
uv run ruff check .
uv run ruff format .

# Type check
uv run mypy app/

# Run tests
uv run pytest

# Pre-commit hooks (ruff check --fix, ruff format, trailing whitespace, etc.)
pre-commit run --all-files
```

## Architecture

The app follows a layered architecture with clear separation between data, logic, and UI:

- **`app/main.py`** — Entry point. Wires together services, calculator, and UI tabs via Streamlit.
- **`app/models/financial_data.py`** — Pydantic domain models: `StockInfo`, `FinancialMetrics`, `NewsItem`, `ChartSeries`. All financial data flows through these typed models.
- **`app/services/stock_service.py`** — `StockService` wraps yfinance calls. All fetches are cached with `@st.cache_data` (5-min TTL). Returns domain models, not raw dicts.
- **`app/services/financial_calculator.py`** — `FinancialCalculator` is pure logic (no UI deps). Takes pandas DataFrames from yfinance, outputs `FinancialMetrics`.
- **`app/ui/base_tab.py`** — `BaseTab` ABC. All dashboard tabs extend this and implement `render(**kwargs)`.
- **`app/ui/tab_*.py`** — One file per tab (Summary, Financials, Prices, Technical, News). Each receives `stock_service`, `info`, `period`, `ticker`, `metrics` via kwargs.
- **`app/ui/sidebar.py`** — Renders the sidebar, returns `(ticker, period)`.
- **`app/config/settings.py`** — `pydantic-settings` loading from `.env`. Key settings: `sentry_dsn`, `environment`, `log_level`.
- **`app/core/logging.py`** — Dual logging: Rich console handler + JSON file handler (`logs/app.json`).
- **`app/core/monitoring.py`** — Optional Sentry integration, no-op if DSN not set.

**Import convention**: Modules use short imports (`from config import settings`, `from models import StockInfo`) because `app/` is the `src` root for ruff and is on the Python path.

## Code Style

- Ruff config in `ruff_base.toml`: line length 110, target Python 3.12, rules include pycodestyle, pyflakes, isort, flake8-comprehensions, flake8-bugbear, pyupgrade.
- Double quotes, space indentation.
- Pre-commit hooks enforce ruff lint+format on every commit.
