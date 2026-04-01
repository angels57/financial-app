import streamlit as st

import yfinance as yf
from core import get_app_logger, init_monitoring
from config import settings
from utils import calculate_52_week_delta

logger = get_app_logger("")


def main():
    st.set_page_config(page_title="Financial Stre", layout="wide")
    init_monitoring(dsn=settings.sentry_dsn, environment=settings.environment)

    st.title("Financial Stre - Stock Price Lookup")

    ticker = st.text_input("Enter stock ticker:", placeholder="AAPL").upper().strip()

    if ticker:
        with st.spinner(f"Fetching {ticker}..."):
            try:
                stock = yf.Ticker(ticker)
                info = stock.fast_info
                full_info = stock.info
                price = info.last_price
                currency = info.currency

                if price is None:
                    st.error(f"Could not find price for ticker: {ticker}")
                    return

                week_52_low = full_info.get("fiftyTwoWeekLow")
                week_52_high = full_info.get("fiftyTwoWeekHigh")
                prev_close = info.previous_close

                st.subheader(f"{ticker} - {full_info.get('shortName', ticker)}")

                col1, col2, col3 = st.columns(3)
                low_delta = calculate_52_week_delta(price, week_52_low)
                high_delta = calculate_52_week_delta(price, week_52_high)
                with col1:
                    st.metric("Current Price", f"{currency} {price:,.2f}")
                with col2:
                    st.metric(
                        "52-Week Low",
                        f"{currency} {week_52_low:,.2f}" if week_52_low else "N/A",
                        f"{low_delta:+.2f}%" if low_delta is not None else None,
                    )
                with col3:
                    st.metric(
                        "52-Week High",
                        f"{currency} {week_52_high:,.2f}" if week_52_high else "N/A",
                        f"{high_delta:+.2f}%" if high_delta is not None else None,
                    )

                st.markdown("---")
                col_tv = st.columns([1, 3])
                with col_tv[0]:
                    st.link_button(
                        "📈 View on TradingView",
                        f"https://www.tradingview.com/symbols/{ticker}/",
                        use_container_width=True,
                    )

                st.subheader("Price History (5 Years)")
                hist = stock.history(period="5y")[["Close"]]
                st.line_chart(hist, use_container_width=True)

                st.subheader("Market Info")

                col4, col5, col6, col7 = st.columns(4)
                col4.metric(
                    "Market Cap",
                    f"{info.market_cap:,.0f}" if info.market_cap else "N/A",
                )
                col5.metric("Exchange", info.exchange or "N/A")
                col6.metric(
                    "Previous Close",
                    f"{currency} {prev_close:,.2f}" if prev_close else "N/A",
                )
                change_pct = (
                    ((price - prev_close) / prev_close * 100) if prev_close else 0
                )
                col7.metric("Daily Change", f"{change_pct:+.2f}%")

                logger.info(f"Retrieved price for {ticker}: {price} {currency}")
            except Exception as e:
                st.error(f"Error fetching data for {ticker}: {str(e)}")
                logger.error(f"Error fetching {ticker}: {str(e)}")


if __name__ == "__main__":
    main()
