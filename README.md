# Financial Stre

Dashboard financiero interactivo construido con Streamlit. Permite analizar acciones bursátiles con resúmenes, estados financieros, valoración, análisis técnico y noticias. Los datos provienen de yfinance (fuente primaria) y Alpha Vantage (fuente secundaria opcional), con cache persistente en PostgreSQL.

## Requisitos Previos

- [Python 3.12+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) — gestor de dependencias
- [Docker](https://www.docker.com/) y Docker Compose (opcional, para PostgreSQL y despliegue)
- [pre-commit](https://pre-commit.com/) (opcional, para hooks de validación)

## Inicio Rápido

### Desarrollo local (sin Docker)

```bash
# Instalar dependencias
uv sync

# Ejecutar la aplicación
uv run streamlit run app/main.py

# (Opcional) Instalar hooks de pre-commit
pre-commit install
```

Sin PostgreSQL configurado, la app funciona en modo degradado usando solo yfinance con cache en memoria de Streamlit.

### Con Docker Compose

```bash
# Levantar PostgreSQL + aplicación
docker compose up -d

# Ver logs
docker compose logs -f web

# Detener todo
docker compose down

# Detener y eliminar volúmenes (borra datos del cache)
docker compose down -v
```

La app estará disponible en `http://localhost:8501`.

## Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Base de datos (opcional — sin ella funciona sin cache persistente)
DB_URL=postgresql://finapp:finapp_local@localhost:5432/financial_stre

# Alpha Vantage (opcional — fuente secundaria para llenar gaps de yfinance)
ALPHA_VANTAGE_API_KEY=tu_api_key_aqui

# Cache de precios (segundos, default: 300 = 5 min)
PRICE_CACHE_TTL_SECONDS=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.json

# Sentry (opcional)
SENTRY_DSN=
ENVIRONMENT=development
```

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `DB_URL` | No | `""` | URL de conexión a PostgreSQL |
| `ALPHA_VANTAGE_API_KEY` | No | `""` | API key de [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (free tier: 5 req/min, 25/día) |
| `PRICE_CACHE_TTL_SECONDS` | No | `300` | TTL del cache de precios en segundos |
| `LOG_LEVEL` | No | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `SENTRY_DSN` | No | `""` | DSN de Sentry para monitoreo de errores |

## Estructura del Proyecto

```
financial-stre/
├── app/
│   ├── main.py                  # Entry point — wiring de servicios, cache y UI
│   ├── config/
│   │   └── settings.py          # pydantic-settings, carga desde .env
│   ├── core/
│   │   ├── logging.py           # Dual logging: Rich (consola) + JSON (archivo)
│   │   └── monitoring.py        # Integración opcional con Sentry
│   ├── db/
│   │   ├── connection.py        # Pool de conexiones PostgreSQL (psycopg3)
│   │   ├── schema.py            # DDL — CREATE TABLE IF NOT EXISTS (idempotente)
│   │   └── cache_repo.py        # CacheRepository — lectura/escritura del cache en DB
│   ├── models/
│   │   └── financial_data.py    # Modelos Pydantic: StockInfo, FinancialMetrics, NewsItem, ChartSeries
│   ├── services/
│   │   ├── stock_service.py     # Wrapper de yfinance (fuente primaria)
│   │   ├── alpha_vantage_service.py  # Cliente Alpha Vantage REST (fuente secundaria)
│   │   ├── data_aggregator.py   # Fachada: cache → yfinance → Alpha Vantage → merge
│   │   └── financial_calculator.py   # Lógica pura de cálculo de métricas financieras
│   ├── ui/
│   │   ├── base_tab.py          # ABC para tabs con safe_render() (error boundary)
│   │   ├── sidebar.py           # Sidebar: ticker input, config, refresh, empresas consultadas
│   │   ├── components.py        # Componentes UI reutilizables
│   │   ├── tab_summary.py       # Tab Resumen: métricas, 52-week range, precio con volumen
│   │   ├── tab_financials.py    # Tab Finanzas: revenue, cash flow, salud financiera, retorno
│   │   ├── tab_prices.py        # Tab Precios: valoración, fair value, rentabilidad
│   │   ├── tab_technical.py     # Tab Análisis Técnico
│   │   └── tab_news.py          # Tab Noticias
│   └── utils/
│       ├── formatters.py        # Formateo de números grandes ($1.2B, $340M)
│       └── stocks.py            # Helpers: CAGR, YoY growth, chart builders (Plotly)
├── tests/                       # Tests unitarios con pytest
├── docker-compose.yml           # PostgreSQL + app
├── Dockerfile                   # Multi-stage build con uv
├── pyproject.toml               # Dependencias y config de herramientas
└── .pre-commit-config.yaml      # Hooks: ruff check, ruff format, trailing whitespace
```

## Arquitectura

```
Sidebar (ticker + periodo + refresh)
    │
    ▼
DataAggregator (fachada)
    ├── CacheRepository (PostgreSQL)  ←── lee primero del cache
    ├── StockService (yfinance)       ←── fuente primaria
    └── AlphaVantageService           ←── fuente secundaria (llena gaps)
    │
    ▼
Tabs (reciben stock_service, info, metrics, period, ticker)
```

### Estrategia de cache

| Tipo de dato | Auto-refresh | Refresh manual | Almacenamiento |
|---|---|---|---|
| Precios | Cada 5 min (configurable) | Sí | `price_cache` |
| Info empresa | No | Sí (botón) | `stock_info_cache` |
| Estados financieros | No | Sí (botón) | `financial_statements_cache` |
| Noticias | No | Sí (botón) | `financial_statements_cache` |

### Degradación graceful

- **Sin PostgreSQL** → yfinance directo + cache en memoria de Streamlit
- **Sin Alpha Vantage API key** → solo yfinance (log de advertencia)
- **Alpha Vantage rate-limited** → se omite silenciosamente, solo yfinance
- **yfinance falla** → intenta Alpha Vantage → si ambos fallan → muestra error

## Comandos

```bash
# Instalar dependencias
uv sync

# Ejecutar la aplicación
uv run streamlit run app/main.py

# Lint
uv run ruff check .

# Formatear código
uv run ruff format .

# Type check
uv run mypy app/

# Tests
uv run pytest

# Pre-commit hooks (lint + format + trailing whitespace)
pre-commit run --all-files
```

## Docker

### Build manual

```bash
docker build -t financial-stre .
docker run -p 8501:8501 financial-stre
```

### Docker Compose (recomendado)

```bash
# Levantar todo (PostgreSQL + app)
docker compose up -d

# Reconstruir después de cambios en código
docker compose up -d --build

# Ver logs en tiempo real
docker compose logs -f web
docker compose logs -f db

# Reiniciar solo la app
docker compose restart web

# Detener
docker compose down

# Detener y borrar datos persistentes
docker compose down -v
```

### Servicios

| Servicio | Puerto | Descripción |
|---|---|---|
| `web` | 8501 | Aplicación Streamlit |
| `db` | 5432 | PostgreSQL 16 (usuario: `finapp`, base: `financial_stre`) |

### Conectar a PostgreSQL manualmente

```bash
# Desde el host (requiere psql instalado)
psql postgresql://finapp:finapp_local@localhost:5432/financial_stre

# Desde el contenedor
docker compose exec db psql -U finapp financial_stre
```

## Fuentes de Datos

### yfinance (primaria)

Proporciona precios, estados financieros, balance, cash flow, dividendos, info de empresa y noticias. Sin necesidad de API key.

### Alpha Vantage (secundaria, opcional)

Complementa yfinance llenando campos vacíos o NaN. Requiere API key gratuita en [alphavantage.co](https://www.alphavantage.co/support/#api-key).

Límites del free tier:
- 5 requests por minuto
- 25 requests por día

Endpoints usados: `OVERVIEW`, `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`.

## Tecnologías

- **Frontend**: Streamlit, Plotly
- **Data**: yfinance, Alpha Vantage REST API
- **Base de datos**: PostgreSQL 16 + psycopg3
- **Modelos**: Pydantic v2, pydantic-settings
- **Herramientas**: uv, Ruff, mypy, pytest, pre-commit, Docker
