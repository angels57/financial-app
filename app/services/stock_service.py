"""Servicio de obtención de datos de acciones desde yfinance."""

import pandas as pd
import streamlit as st
import yfinance as yf

from models import NewsItem, StockInfo

CACHE_TTL = 300  # 5 minutos


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_info(ticker: str) -> StockInfo:
    stock = yf.Ticker(ticker)
    info = stock.fast_info
    full_info = stock.info
    fcf = full_info.get("freeCashflow")
    shares = full_info.get("sharesOutstanding")
    price_to_fcf = None
    if fcf and shares and fcf > 0:
        price_to_fcf = (info.last_price * shares) / fcf
    return StockInfo(
        ticker=ticker,
        short_name=full_info.get("shortName", ticker),
        price=info.last_price,
        currency=info.currency,
        market_cap=info.market_cap,
        pe_ratio=full_info.get("trailingPE"),
        volume=info.last_volume,
        week_52_low=full_info.get("fiftyTwoWeekLow"),
        week_52_high=full_info.get("fiftyTwoWeekHigh"),
        sector=full_info.get("sector", ""),
        industry=full_info.get("industry", ""),
        country=full_info.get("country", ""),
        employees=full_info.get("fullTimeEmployees"),
        website=full_info.get("website", ""),
        description=full_info.get("longBusinessSummary", ""),
        beta=full_info.get("beta"),
        dividend_yield=full_info.get("dividendYield"),
        eps=full_info.get("trailingEps"),
        target_price=full_info.get("targetMeanPrice"),
        recommendation=full_info.get("recommendationKey", ""),
        shares_outstanding=full_info.get("sharesOutstanding"),
        forward_pe=full_info.get("forwardPE"),
        price_to_sales=full_info.get("priceToSalesTrailing12Months"),
        price_to_fcf=price_to_fcf,
        total_revenue=full_info.get("totalRevenue"),
        free_cash_flow=full_info.get("freeCashflow"),
        net_income=full_info.get("netIncomeToCommon"),
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_history(ticker: str, period: str) -> pd.DataFrame:
    return yf.Ticker(ticker).history(period=period)[["Close"]]


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_financials(ticker: str) -> pd.DataFrame | None:
    df = yf.Ticker(ticker).financials
    if df is None or df.empty:
        return None
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_balance_sheet(ticker: str) -> pd.DataFrame | None:
    df = yf.Ticker(ticker).balance_sheet
    if df is None or df.empty:
        return None
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_cashflow(ticker: str) -> pd.DataFrame | None:
    df = yf.Ticker(ticker).cashflow
    if df is None or df.empty:
        return None
    return df


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _fetch_news(ticker: str) -> list[dict]:
    try:
        return yf.Ticker(ticker).news or []
    except Exception:
        return []


class StockService:
    """Responsabilidad única: obtener datos crudos de yfinance."""

    def __init__(self, ticker: str):
        self._ticker_symbol = ticker

    @property
    def ticker(self) -> str:
        return self._ticker_symbol

    def get_info(self) -> StockInfo:
        return _fetch_info(self._ticker_symbol)

    def get_history(self, period: str) -> pd.DataFrame:
        return _fetch_history(self._ticker_symbol, period)

    def get_financials(self) -> pd.DataFrame | None:
        return _fetch_financials(self._ticker_symbol)

    def get_balance_sheet(self) -> pd.DataFrame | None:
        return _fetch_balance_sheet(self._ticker_symbol)

    def get_cashflow(self) -> pd.DataFrame | None:
        return _fetch_cashflow(self._ticker_symbol)

    def get_news(self) -> list[NewsItem]:
        raw_news = _fetch_news(self._ticker_symbol)
        items = []
        for item in raw_news[:5]:
            content = item.get("content", item)
            title = content.get("title")
            click_url = content.get("clickThroughUrl") or {}
            link = click_url.get("url") if isinstance(click_url, dict) else None
            if not link:
                canonical = content.get("canonicalUrl") or {}
                link = canonical.get("url") if isinstance(canonical, dict) else None
            if not title or not link:
                continue
            provider = content.get("provider") or {}
            publisher = (
                provider.get("displayName", "Fuente desconocida")
                if isinstance(provider, dict)
                else "Fuente desconocida"
            )
            thumbnail_data = content.get("thumbnail") or {}
            thumbnail = ""
            if isinstance(thumbnail_data, dict):
                resolutions = thumbnail_data.get("resolutions") or []
                if resolutions:
                    thumbnail = resolutions[0].get("url", "")
                else:
                    thumbnail = thumbnail_data.get("originalUrl", "")
            items.append(
                NewsItem(
                    title=title,
                    link=link,
                    publisher=publisher,
                    thumbnail=thumbnail,
                    published_at=content.get("pubDate", ""),
                )
            )
        return items
