"""YFinance data mapper — converts yfinance raw data to domain models."""

from __future__ import annotations

from domain.models import NewsItem, StockInfo


class YFinanceMapper:
    """Maps yfinance raw data to domain models."""

    @staticmethod
    def to_stock_info(ticker: str, yf_info: dict, yf_ticker) -> StockInfo:
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
            dividend_yield=yf_info.get("dividendYield"),
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
    def to_news_items(ticker: str, yf_news: list) -> list[NewsItem]:
        """Convert yfinance news to NewsItem domain models."""
        items = []
        for item in yf_news:
            thumbnail = ""
            if "thumbnail" in item:
                res = item["thumbnail"].get("resolutions", [])
                if res:
                    thumbnail = res[-1].get("url", "")

            items.append(
                NewsItem(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    publisher=item.get("publisher", "Fuente desconocida"),
                    thumbnail=thumbnail,
                    published_at=item.get("providerPublishTime", ""),
                )
            )
        return items
