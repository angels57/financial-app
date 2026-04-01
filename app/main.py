import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf

from core import get_app_logger, init_monitoring
from config import settings
from utils import calculate_52_week_delta, draw_bar_chart, format_large_number

logger = get_app_logger("")


def main():
    st.set_page_config(
        page_title="Financial Stre", layout="wide", initial_sidebar_state="expanded"
    )
    init_monitoring(dsn=settings.sentry_dsn, environment=settings.environment)

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🚀 Financial Stre")
        st.markdown("---")
        ticker = (
            st.text_input("Buscar Ticker:", value="AAPL", placeholder="Ej: AAPL, TSLA")
            .upper()
            .strip()
        )

        st.subheader("Configuración")
        period = st.selectbox(
            "Periodo Histórico", options=["1y", "2y", "5y", "10y", "max"], index=2
        )

        st.markdown("---")
        st.info(
            "Introduce un símbolo de cotización para analizar su rendimiento y estados financieros."
        )

    if not ticker:
        st.title("Bienvenido a Financial Stre")
        st.info(
            "Por favor, introduce un ticker en el panel de la izquierda para comenzar."
        )
        return

    # --- DATA FETCHING ---
    with st.spinner(f"Cargando datos de {ticker}..."):
        try:
            stock = yf.Ticker(ticker)
            info = stock.fast_info
            full_info = stock.info
            price = info.last_price
            currency = info.currency

            if price is None:
                st.error(f"No se pudo encontrar el precio para: {ticker}")
                return

            # --- HEADER ---
            st.title(f"{full_info.get('shortName', ticker)} ({ticker})")

            # --- TABS ---
            tab_summary, tab_financials, tab_tech, tab_news = st.tabs(
                ["📊 Resumen", "📈 Finanzas", "🔬 Análisis Técnico", "📰 Noticias"]
            )

            # --- TAB 1: RESUMEN ---
            with tab_summary:
                col1, col2, col3 = st.columns(3)
                low_52 = full_info.get("fiftyTwoWeekLow")
                high_52 = full_info.get("fiftyTwoWeekHigh")
                low_delta = calculate_52_week_delta(price, low_52)
                high_delta = calculate_52_week_delta(price, high_52)

                with col1:
                    st.metric("Precio Actual", f"{currency} {price:,.2f}")
                with col2:
                    st.metric(
                        "Mínimo 52 Semanas",
                        f"{currency} {low_52:,.2f}" if low_52 else "N/A",
                        f"{low_delta:+.2f}%" if low_delta else None,
                    )
                with col3:
                    st.metric(
                        "Máximo 52 Semanas",
                        f"{currency} {high_52:,.2f}" if high_52 else "N/A",
                        f"{high_delta:+.2f}%" if high_delta else None,
                    )

                st.markdown("---")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Market Cap", format_large_number(info.market_cap, currency))
                pe_ratio = full_info.get("trailingPE")
                c2.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                c3.metric("Volumen", f"{info.last_volume:,.0f}")
                with c4:
                    st.link_button(
                        "📈 Ver en TradingView",
                        f"https://www.tradingview.com/symbols/{ticker}/",
                        use_container_width=True,
                    )

                st.subheader(f"Historial de Precios ({period})")
                hist = stock.history(period=period)[["Close"]]
                if not hist.empty:
                    fig, ax = plt.subplots(figsize=(12, 4))
                    ax.plot(hist.index, hist["Close"], color="#1f77b4", linewidth=1.5)
                    ax.fill_between(hist.index, hist["Close"], alpha=0.1)
                    ax.set_ylabel(f"Precio ({currency})")
                    ax.grid(True, alpha=0.2)
                    st.pyplot(fig, use_container_width=True)
                else:
                    st.warning("No hay datos históricos para este periodo.")

            # --- TAB 2: FINANZAS ---
            with tab_financials:
                st.subheader("Rendimiento Financiero Anual")
                financials = stock.financials
                cashflow = stock.cashflow

                if financials is not None and not financials.empty:
                    col_f1, col_f2 = st.columns(2)

                    with col_f1:
                        if "Total Revenue" in financials.index:
                            rev = financials.loc["Total Revenue"].iloc[:5]
                            fig_rev = draw_bar_chart(
                                rev.values / 1e9,
                                [str(d.year) for d in rev.index],
                                "Ingresos Anuales",
                                "Billions ($)",
                            )
                            st.pyplot(fig_rev, use_container_width=True)

                    with col_f2:
                        if (
                            "Net Income" in financials.index
                            and "Total Revenue" in financials.index
                        ):
                            rev = financials.loc["Total Revenue"].iloc[:5]
                            ni = financials.loc["Net Income"].iloc[:5]
                            margin = (ni.values / rev.values) * 100
                            fig_margin = draw_bar_chart(
                                margin,
                                [str(d.year) for d in rev.index],
                                "Margen Neto (%)",
                                "Porcentaje",
                                signed=True,
                                is_percent=True,
                            )
                            st.pyplot(fig_margin, use_container_width=True)

                    st.markdown("---")
                    col_f3, col_f4 = st.columns(2)

                    with col_f3:
                        if (
                            cashflow is not None
                            and not cashflow.empty
                            and "Free Cash Flow" in cashflow.index
                        ):
                            fcf = cashflow.loc["Free Cash Flow"].iloc[:5]
                            fig_fcf = draw_bar_chart(
                                fcf.values / 1e9,
                                [str(d.year) for d in fcf.index],
                                "Free Cash Flow",
                                "Billions ($)",
                                signed=True,
                            )
                            st.pyplot(fig_fcf, use_container_width=True)
                        else:
                            st.info("Datos de Free Cash Flow no disponibles.")

                    with col_f4:
                        st.info("Próximamente: Análisis de Deuda y EBITDA")
                else:
                    st.warning(
                        "No hay datos financieros anuales disponibles para este ticker."
                    )

            # --- TAB 3: ANÁLISIS TÉCNICO ---
            with tab_tech:
                st.subheader("Indicadores Técnicos")
                st.info(
                    "Sección en desarrollo. Aquí se mostrarán RSI, MACD y Medias Móviles."
                )

            # --- TAB 4: NOTICIAS ---
            with tab_news:
                st.subheader(f"Últimas Noticias de {ticker}")
                try:
                    news = stock.news
                    if news:
                        for item in news[:5]:
                            title = item.get("title")
                            link = item.get("link")
                            publisher = item.get("publisher", "Fuente desconocida")

                            if title and link:
                                with st.container():
                                    st.write(f"**{title}**")
                                    st.caption(
                                        f"Fuente: {publisher} | [Leer más]({link})"
                                    )
                                    st.markdown("---")
                    else:
                        st.info(
                            "No se encontraron noticias recientes para este ticker."
                        )
                except Exception as news_err:
                    st.warning("No se pudieron cargar las noticias en este momento.")
                    logger.warning(
                        f"Error al cargar noticias de {ticker}: {str(news_err)}"
                    )

            logger.info(f"Dashboard actualizado para {ticker}")

        except Exception as e:
            st.error(f"Error al obtener datos: {str(e)}")
            logger.error(f"Error en main: {str(e)}")


if __name__ == "__main__":
    main()
