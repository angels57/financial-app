"""YFinance data mapper — converts yfinance raw data to domain models."""

from __future__ import annotations

from typing import Any

from app.domain.models import NewsItem, StockInfo


class YFinanceMapper:
    """Maps yfinance raw data to domain models."""

    @staticmethod
    def to_stock_info(
        ticker: str, yf_info: dict[str, Any], yf_ticker: Any
    ) -> StockInfo:
        """Convert yfinance info dict to StockInfo domain model."""
        price = yf_info.get("currentPrice") or yf_info.get("regularMarketPrice")
        if price is None:
            price = yf_info.get("previousClose", 0.0)

        volume = yf_info.get("regularMarketVolume")
        if volume is None:
            volume = 0

        shares = yf_info.get("sharesOutstanding")
        if shares is None:
            shares = yf_info.get("impliedSharesOutstanding")

        tar = yf_info.get("trailingAnnualDividendRate", 0)
        div_yield = tar / price if price and tar else None

        return StockInfo(
            ticker=ticker,
            short_name=yf_info.get("shortName", ticker),
            price=float(price),
            currency=yf_info.get("currency", "USD"),
            market_cap=yf_info.get("marketCap"),
            pe_ratio=yf_info.get("trailingPE"),
            volume=int(volume),
            week_52_low=yf_info.get("fiftyTwoWeekLow"),
            week_52_high=yf_info.get("fiftyTwoWeekHigh"),
            sector=yf_info.get("sector", ""),
            industry=yf_info.get("industry", ""),
            country=yf_info.get("country", ""),
            employees=yf_info.get("fullTimeEmployees"),
            website=yf_info.get("website", ""),
            description=yf_info.get("longBusinessSummary", ""),
            beta=yf_info.get("beta"),
            dividend_yield=div_yield,
            eps=yf_info.get("trailingEps"),
            target_price=yf_info.get("targetMeanPrice"),
            recommendation=yf_info.get("recommendationKey", ""),
            shares_outstanding=float(shares) if shares else None,
            forward_pe=yf_info.get("forwardPE"),
            price_to_sales=yf_info.get("priceToSalesTrailing12Months"),
            price_to_fcf=yf_info.get("priceToFreeCashFlow"),
            total_revenue=yf_info.get("totalRevenue"),
            free_cash_flow=yf_info.get("freeCashflow"),
            net_income=yf_info.get("netIncomeToCommon"),
        )

    @staticmethod
    def to_news_items(ticker: str, yf_news: list[dict[str, Any]]) -> list[NewsItem]:
        """Convert yfinance news to NewsItem domain models."""
        items = []
        for item in yf_news:
            content = item.get("content", {})
            thumbnail = ""
            thumb = content.get("thumbnail")
            if thumb:
                res = thumb.get("resolutions", [])
                if res:
                    thumbnail = res[-1].get("url", "")

            title = content.get("title", "")
            link = content.get("canonicalUrl", {}).get("url", "") or content.get(
                "clickThroughUrl", {}
            ).get("url", "")
            if not title or not link:
                continue

            publisher = content.get("provider", {}).get(
                "displayName", "Fuente desconocida"
            )

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
