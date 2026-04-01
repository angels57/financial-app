import streamlit as st
import matplotlib.pyplot as plt

import yfinance as yf
from core import get_app_logger, init_monitoring
from config import settings
from utils import calculate_52_week_delta, format_large_number

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
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(hist.index, hist["Close"], color="#1f77b4", linewidth=1.5)
                ax.set_title(f"{ticker} - 5 Year Price History", fontsize=14)
                ax.set_xlabel("Date")
                ax.set_ylabel(f"Price ({currency})")
                ax.grid(True, alpha=0.3)
                fig.autofmt_xdate()
                st.pyplot(fig, use_container_width=True)

                st.subheader("Annual Revenue (5 Years)")
                financials = stock.financials
                if financials is not None and not financials.empty:
                    if "Total Revenue" in financials.index:
                        revenue = financials.loc["Total Revenue"].iloc[:5]
                        fig2, ax2 = plt.subplots(figsize=(12, 4))
                        years = [str(d.year) for d in revenue.index]
                        ax2.bar(years, revenue.values / 1_000_000_000, color="#2ca02c")
                        ax2.set_title(f"{ticker} - Annual Revenue", fontsize=14)
                        ax2.set_xlabel("Year")
                        ax2.set_ylabel("Revenue (Billions)")
                        ax2.grid(True, alpha=0.3, axis="y")
                        for i, v in enumerate(revenue.values / 1_000_000_000):
                            ax2.text(i, v + 1, f"${v:.1f}B", ha="center", fontsize=9)
                        st.pyplot(fig2, use_container_width=True)
                    else:
                        st.info("Revenue data not available for this ticker.")
                else:
                    st.info("Financial data not available for this ticker.")

                st.subheader("Market Info")

                col4, col5, col6, col7 = st.columns(4)
                col4.metric(
                    "Market Cap", format_large_number(info.market_cap, currency)
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
