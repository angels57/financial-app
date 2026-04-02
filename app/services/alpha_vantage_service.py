"""Alpha Vantage data service — secondary source for financial data."""

import logging
import time
from collections import deque

import pandas as pd
import requests

from models import StockInfo

logger = logging.getLogger(__name__)

# Rate limits: 5 requests per minute, 25 per day (free tier)
_MAX_PER_MINUTE = 5
_MAX_PER_DAY = 25
_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageService:
    """Fetches financial data from Alpha Vantage REST API."""

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._minute_calls: deque[float] = deque()
        self._daily_calls: deque[float] = deque()

    def _can_call(self) -> bool:
        now = time.time()
        # Clean old entries
        while self._minute_calls and now - self._minute_calls[0] > 60:
            self._minute_calls.popleft()
        while self._daily_calls and now - self._daily_calls[0] > 86400:
            self._daily_calls.popleft()
        if len(self._minute_calls) >= _MAX_PER_MINUTE:
            logger.warning("Alpha Vantage rate limit (per minute) reached")
            return False
        if len(self._daily_calls) >= _MAX_PER_DAY:
            logger.warning("Alpha Vantage rate limit (daily) reached")
            return False
        return True

    def _request(self, **params) -> dict | None:
        if not self._can_call():
            return None
        params["apikey"] = self._api_key
        try:
            now = time.time()
            resp = requests.get(_BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            self._minute_calls.append(now)
            self._daily_calls.append(now)
            data = resp.json()
            if "Error Message" in data or "Note" in data:
                logger.warning(
                    "Alpha Vantage error: %s",
                    data.get("Error Message") or data.get("Note"),
                )
                return None
            return data
        except Exception:
            logger.exception("Alpha Vantage request failed")
            return None

    # -- Public API -----------------------------------------------------------

    def get_info(self, ticker: str) -> StockInfo | None:
        data = self._request(function="OVERVIEW", symbol=ticker)
        if not data or "Symbol" not in data:
            return None

        def _float(key: str) -> float | None:
            val = data.get(key)
            if val is None or val == "None" or val == "-":
                return None
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        def _int(key: str) -> int | None:
            val = data.get(key)
            if val is None or val == "None" or val == "-":
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        div_yield = _float("DividendYield")

        return StockInfo(
            ticker=ticker,
            short_name=data.get("Name", ticker),
            price=0.0,  # AV OVERVIEW doesn't include current price
            currency=data.get("Currency", "USD"),
            market_cap=_float("MarketCapitalization"),
            pe_ratio=_float("PERatio"),
            volume=0,
            sector=data.get("Sector", ""),
            industry=data.get("Industry", ""),
            country=data.get("Country", ""),
            employees=_int("FullTimeEmployees"),
            website=data.get("Address", ""),
            description=data.get("Description", ""),
            beta=_float("Beta"),
            dividend_yield=div_yield,
            eps=_float("EPS"),
            target_price=_float("AnalystTargetPrice"),
            forward_pe=_float("ForwardPE"),
            price_to_sales=_float("PriceToSalesRatioTTM"),
        )

    def get_financials(self, ticker: str) -> pd.DataFrame | None:
        return self._fetch_statement(ticker, "INCOME_STATEMENT", "annualReports")

    def get_balance_sheet(self, ticker: str) -> pd.DataFrame | None:
        return self._fetch_statement(ticker, "BALANCE_SHEET", "annualReports")

    def get_cashflow(self, ticker: str) -> pd.DataFrame | None:
        return self._fetch_statement(ticker, "CASH_FLOW", "annualReports")

    # -- Private helpers ------------------------------------------------------

    # Map Alpha Vantage field names to yfinance-compatible names
    _FIELD_MAP = {
        # Income Statement
        "totalRevenue": "Total Revenue",
        "costOfRevenue": "Cost Of Revenue",
        "grossProfit": "Gross Profit",
        "researchAndDevelopment": "Research And Development",
        "sellingGeneralAndAdministrative": "Selling General And Administration",
        "operatingIncome": "Operating Income",
        "interestExpense": "Interest Expense",
        "incomeBeforeTax": "Pretax Income",
        "incomeTaxExpense": "Tax Provision",
        "netIncome": "Net Income",
        "ebitda": "EBITDA",
        # Balance Sheet
        "totalShareholderEquity": "Stockholders Equity",
        "shortLongTermDebtTotal": "Total Debt",
        "longTermDebt": "Long Term Debt",
        "totalCurrentAssets": "Total Current Assets",
        "totalCurrentLiabilities": "Total Current Liabilities",
        # Cash Flow
        "operatingCashflow": "Operating Cash Flow",
        "capitalExpenditures": "Capital Expenditure",
        "freeCashFlow": "Free Cash Flow",
    }

    def _fetch_statement(
        self, ticker: str, function: str, report_key: str
    ) -> pd.DataFrame | None:
        data = self._request(function=function, symbol=ticker)
        if not data or report_key not in data:
            return None
        reports = data[report_key]
        if not reports:
            return None

        records: dict[str, dict] = {}
        for report in reports[:5]:
            date = report.get("fiscalDateEnding", "")
            if not date:
                continue
            col = pd.Timestamp(date)
            for av_key, yf_key in self._FIELD_MAP.items():
                val = report.get(av_key)
                if val is not None and val != "None":
                    try:
                        records.setdefault(yf_key, {})[col] = float(val)
                    except (ValueError, TypeError):
                        pass

        if not records:
            return None
        return pd.DataFrame(records).T
