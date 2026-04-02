"""Servicio de obtención de datos de acciones desde yfinance."""

import pandas as pd
import yfinance as yf

from models import NewsItem, StockInfo


class StockService:
    """Responsabilidad única: obtener datos crudos de yfinance."""

    def __init__(self, ticker: str):
        self._ticker_symbol = ticker
        self._stock = yf.Ticker(ticker)

    @property
    def ticker(self) -> str:
        return self._ticker_symbol

    def get_info(self) -> StockInfo:
        info = self._stock.fast_info
        full_info = self._stock.info
        return StockInfo(
            ticker=self._ticker_symbol,
            short_name=full_info.get("shortName", self._ticker_symbol),
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
        )

    def get_history(self, period: str) -> pd.DataFrame:
        return self._stock.history(period=period)[["Close"]]

    def get_financials(self) -> pd.DataFrame | None:
        df = self._stock.financials
        if df is None or df.empty:
            return None
        return df

    def get_balance_sheet(self) -> pd.DataFrame | None:
        df = self._stock.balance_sheet
        if df is None or df.empty:
            return None
        return df

    def get_cashflow(self) -> pd.DataFrame | None:
        df = self._stock.cashflow
        if df is None or df.empty:
            return None
        return df

    def get_news(self) -> list[NewsItem]:
        try:
            raw_news = self._stock.news or []
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
        except Exception:
            return []
