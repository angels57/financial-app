"""Tab de análisis técnico con SMA y RSI."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from models import StockInfo
from ui.base_tab import BaseTab


class TechnicalTab(BaseTab):
    """Renderiza el tab de análisis técnico con SMA y RSI."""

    SMA_PERIODS = [50, 100, 200]
    SMA_COLORS = {50: "#ff7f0e", 100: "#7f7f7f", 200: "#2ca02c"}
    SMA_WIDTHS = {50: 2.0, 100: 1.5, 200: 1.0}
    RSI_PERIOD = 14

    def render(self, *, stock_service, info: StockInfo, period: str, **kwargs) -> None:
        st.subheader("Análisis Técnico")

        col_int, col_periods = st.columns([1, 3])
        with col_int:
            interval = st.selectbox(
                "Intervalo",
                options=["daily", "weekly"],
                index=0,
                key="tech_interval",
            )

        st.write("Períodos SMA:")
        col_50, col_100, col_200 = st.columns([1, 1, 1])
        with col_50:
            show_50 = st.checkbox("SMA 50", value=True, key="sma_50")
        with col_100:
            show_100 = st.checkbox("SMA 100", value=True, key="sma_100")
        with col_200:
            show_200 = st.checkbox("SMA 200", value=True, key="sma_200")

        selected_periods = []
        if show_50:
            selected_periods.append(50)
        if show_100:
            selected_periods.append(100)
        if show_200:
            selected_periods.append(200)

        st.markdown("---")

        if not selected_periods:
            st.warning("Selecciona al menos un período SMA.")
            return

        with st.spinner("Cargando indicadores..."):
            sma_data, rsi_data = self._fetch_indicator_data(
                stock_service, interval, selected_periods
            )

        hist = stock_service.get_history(period=period)

        if not sma_data or rsi_data is None:
            self._render_no_data_message()
        elif hist.empty:
            st.warning("No hay datos de precio disponibles.")
        else:
            self._render_combined_chart(
                hist, sma_data, rsi_data, info.currency, interval
            )
            self._render_combined_signals(hist, sma_data, rsi_data)
            self._render_cross_alert(sma_data)

        st.markdown("---")
        self._render_indicator_info(interval)

    def _fetch_indicator_data(
        self,
        stock_service,
        interval: str,
        selected_periods: list[int],
    ) -> tuple[dict[int, dict[str, float] | None], dict[str, float] | None]:
        sma_data: dict[int, dict[str, float] | None] = {}
        rsi_data: dict[str, float] | None = None

        if selected_periods:
            sma_data = stock_service.get_multiple_sma(
                periods=selected_periods, interval=interval
            )
        rsi_data = stock_service.get_rsi(time_period=self.RSI_PERIOD, interval=interval)

        return sma_data, rsi_data

    def _render_sma_chart(
        self,
        hist: pd.DataFrame,
        sma_data: dict[int, dict[str, float] | None],
        currency: str,
        interval: str,
    ) -> None:
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.75, 0.25],
        )

        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Precio",
                line={"color": "#1f77b4", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(31,119,180,0.1)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} "
                + currency
                + "<extra></extra>",
            ),
            row=1,
            col=1,
        )

        for period in self.SMA_PERIODS:
            data = sma_data.get(period)
            if data is None:
                continue
            sorted_dates = sorted(data.keys())
            values = [data[d] for d in sorted_dates]
            dates_pd = pd.to_datetime(sorted_dates)

            fig.add_trace(
                go.Scatter(
                    x=dates_pd,
                    y=values,
                    mode="lines",
                    name=f"SMA {period}",
                    line={
                        "color": self.SMA_COLORS[period],
                        "width": self.SMA_WIDTHS[period],
                    },
                    hovertemplate="%{x|%d %b %Y}<br>SMA "
                    + str(period)
                    + ": %{y:,.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

        if "Volume" in hist.columns:
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist["Volume"],
                    name="Volumen",
                    marker_color="rgba(31,119,180,0.3)",
                    hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>",
                ),
                row=2,
                col=1,
            )

        fig.update_layout(
            xaxis2={
                "rangeselector": {
                    "buttons": [
                        {"count": 1, "label": "1M", "step": "month"},
                        {"count": 3, "label": "3M", "step": "month"},
                        {"count": 6, "label": "6M", "step": "month"},
                        {
                            "count": 1,
                            "label": "YTD",
                            "step": "year",
                            "stepmode": "todate",
                        },
                        {"count": 1, "label": "1Y", "step": "year"},
                        {"label": "Todo", "step": "all"},
                    ]
                },
                "rangeslider": {"visible": True},
            },
            yaxis_title=f"Precio ({currency})",
            yaxis2_title="Volumen",
            hovermode="x unified",
            height=600,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        st.plotly_chart(fig, width="stretch")

    def _render_sma_signals(
        self, hist: pd.DataFrame, sma_data: dict[int, dict[str, float] | None]
    ) -> None:
        if hist.empty:
            return

        latest_price = hist["Close"].iloc[-1]

        metrics_cols = st.columns(len(self.SMA_PERIODS) + 1)
        with metrics_cols[0]:
            st.metric(
                "Precio Actual",
                f"${latest_price:,.2f}" if latest_price > 0 else "N/A",
            )

        for i, period in enumerate(self.SMA_PERIODS):
            data = sma_data.get(period)
            if data is None:
                with metrics_cols[i + 1]:
                    st.metric(f"SMA {period}", "N/A")
                continue

            sorted_dates = sorted(data.keys(), reverse=True)
            if not sorted_dates:
                with metrics_cols[i + 1]:
                    st.metric(f"SMA {period}", "N/A")
                continue

            latest_sma = data.get(sorted_dates[0], 0)
            if latest_sma > 0:
                pct_diff = ((latest_price - latest_sma) / latest_sma) * 100
                signal = "▲" if pct_diff > 0 else "▼"
            else:
                pct_diff = 0
                signal = ""

            with metrics_cols[i + 1]:
                st.metric(
                    f"SMA {period}",
                    f"${latest_sma:,.2f}" if latest_sma > 0 else "N/A",
                    f"{signal}{abs(pct_diff):.2f}%" if latest_sma > 0 else None,
                )

    def _detect_crossover(
        self, sma_data: dict[int, dict[str, float] | None]
    ) -> tuple[str | None, str | None]:
        sma_50 = sma_data.get(50)
        sma_200 = sma_data.get(200)

        if sma_50 is None or sma_200 is None:
            return None, None

        dates_50 = sorted(sma_50.keys(), reverse=True)
        dates_200 = sorted(sma_200.keys(), reverse=True)
        common_dates = sorted(set(dates_50) & set(dates_200), reverse=True)

        if len(common_dates) < 2:
            return None, None

        for i in range(min(30, len(common_dates) - 1)):
            curr_date = common_dates[i]
            prev_date = common_dates[i + 1]

            curr_50 = sma_50.get(curr_date, 0)
            curr_200 = sma_200.get(curr_date, 0)
            prev_50 = sma_50.get(prev_date, 0)
            prev_200 = sma_200.get(prev_date, 0)

            if curr_50 == 0 or curr_200 == 0 or prev_50 == 0 or prev_200 == 0:
                continue

            curr_50_above = curr_50 > curr_200
            prev_50_above = prev_50 > prev_200

            if curr_50_above and not prev_50_above:
                return "GOLDEN_CROSS", curr_date
            elif not curr_50_above and prev_50_above:
                return "DEATH_CROSS", curr_date

        return None, None

    def _render_cross_alert(self, sma_data: dict[int, dict[str, float] | None]) -> None:
        cross_type, cross_date = self._detect_crossover(sma_data)

        if cross_type == "GOLDEN_CROSS":
            st.success(
                f"🟡 **GOLDEN CROSS detectado el {cross_date}** — "
                "SMA 50 cruzó por encima de SMA 200. Señal alcista de largo plazo."
            )
        elif cross_type == "DEATH_CROSS":
            st.error(
                f"🔴 **DEATH CROSS detectado el {cross_date}** — "
                "SMA 50 cruzó por debajo de SMA 200. Señal bajista de largo plazo."
            )

    def _render_rsi_chart(
        self,
        hist: pd.DataFrame,
        rsi_data: dict[str, float],
        currency: str,
        time_period: int,
        interval: str,
    ) -> None:
        if hist.empty:
            st.warning("No hay datos de precio disponibles.")
            return

        rsi_dates = sorted(rsi_data.keys())
        rsi_values = [rsi_data[d] for d in rsi_dates]
        rsi_dates_pd = pd.to_datetime(rsi_dates)

        price_hist = hist[hist.index.isin(rsi_dates_pd)]

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.4, 0.6],
        )

        fig.add_trace(
            go.Scatter(
                x=price_hist.index,
                y=price_hist["Close"],
                mode="lines",
                name="Precio",
                line={"color": "#1f77b4", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(31,119,180,0.1)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} "
                + currency
                + "<extra></extra>",
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=rsi_dates_pd,
                y=rsi_values,
                mode="lines",
                name=f"RSI {time_period}",
                line={"color": "#7f7f7f", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(127,127,127,0.2)",
                hovertemplate="%{x|%d %b %Y}<br>RSI: %{y:.2f}<extra></extra>",
            ),
            row=2,
            col=1,
        )

        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="#d62728",
            row=2,
            col=1,
            annotation_text="Sobrecompra (70)",
            annotation_position="bottom right",
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="#2ca02c",
            row=2,
            col=1,
            annotation_text="Sobreventa (30)",
            annotation_position="top right",
        )
        fig.add_hline(y=50, line_dash="dot", line_color="#999999", row=2, col=1)

        fig.update_layout(
            xaxis2={
                "rangeselector": {
                    "buttons": [
                        {"count": 1, "label": "1M", "step": "month"},
                        {"count": 3, "label": "3M", "step": "month"},
                        {"count": 6, "label": "6M", "step": "month"},
                        {
                            "count": 1,
                            "label": "YTD",
                            "step": "year",
                            "stepmode": "todate",
                        },
                        {"count": 1, "label": "1Y", "step": "year"},
                        {"label": "Todo", "step": "all"},
                    ]
                },
                "rangeslider": {"visible": True},
            },
            yaxis_title=f"Precio ({currency})",
            yaxis2_title=f"RSI {time_period}",
            hovermode="x unified",
            height=600,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        fig.update_yaxes(range=[0, 100], row=2, col=1)

        st.plotly_chart(fig, width="stretch")

    def _render_rsi_signals(self, rsi_data: dict[str, float], time_period: int) -> None:
        if not rsi_data:
            return

        sorted_dates = sorted(rsi_data.keys(), reverse=True)
        latest_date = sorted_dates[0]
        latest_rsi = rsi_data.get(latest_date, 0)

        if len(sorted_dates) > 1:
            prev_rsi = rsi_data.get(sorted_dates[1], 0)
        else:
            prev_rsi = latest_rsi

        if latest_rsi > 70:
            signal_color = "#d62728"
            signal_text = "SOBRECOMPRA"
            interpretation = (
                f"RSI en {latest_rsi:.2f} indica sobrecompra. "
                "Posible corrección a la baja o reversión de tendencia."
            )
        elif latest_rsi < 30:
            signal_color = "#2ca02c"
            signal_text = "SOBREVENTA"
            interpretation = (
                f"RSI en {latest_rsi:.2f} indica sobreventa. "
                "Posible rebote o reversión alcista."
            )
        else:
            signal_color = "#7f7f7f"
            signal_text = "NEUTRAL"
            interpretation = (
                f"RSI en {latest_rsi:.2f} está en zona neutral. "
                "Sin señales claras de sobrecompra/sobreventa."
            )

        rsi_delta = latest_rsi - prev_rsi if prev_rsi else 0

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                f"RSI {time_period}",
                f"{latest_rsi:.2f}",
                f"{rsi_delta:+.2f}" if rsi_delta else None,
            )
        with c2:
            st.markdown(
                f"<div style='text-align:center; padding:10px; background-color:{signal_color}; "
                f"color:white; border-radius:5px; font-weight:bold;'>{signal_text}</div>",
                unsafe_allow_html=True,
            )
            zone = (
                "sobrecompra"
                if latest_rsi > 70
                else "sobreventa"
                if latest_rsi < 30
                else "neutral"
            )
            st.caption(f"Zona: {zone}")
        with c3:
            if latest_rsi > 70:
                st.metric("Interpretación", "Vender / Precaución")
            elif latest_rsi < 30:
                st.metric("Interpretación", "Comprar / Oportunidad")
            else:
                st.metric("Interpretación", "Neutral")

        st.info(interpretation)

    def _render_indicator_info(self, interval: str) -> None:
        st.markdown(
            f"""
            **SMA (Simple Moving Average) — Media Móvil Simple**

            Las SMAs son promedios aritméticos de los últimos N puntos de datos
            del precio de cierre en el intervalo {interval}.

            - **SMA 50**: Tendencia a corto/mediano plazo
            - **SMA 100**: Tendencia intermedia
            - **SMA 200**: Tendencia a largo plazo (soporte/resistencia clave)

            **Señales de trading:**
            - Precio **por encima** de una SMA → Tendencia alcista
            - Precio **por debajo** de una SMA → Tendencia bajista
            - **Golden Cross**: SMA 50 cruza **por encima** de SMA 200 → Señal de compra
            - **Death Cross**: SMA 50 cruza **por debajo** de SMA 200 → Señal de venta

            ---

            **RSI (Relative Strength Index) — Índice de Fuerza Relativa**

            El RSI mide la velocidad y magnitud de los cambios de precio,
            oscilando entre 0 y 100.

            - **RSI > 70**: Zona de sobrecompra — posible sobrevaloración
            - **RSI < 30**: Zona de sobreventa — posible infravaloración
            - **RSI ~ 50**: Equilibrio entre compradores y vendedores

            **Interpretación:**
            - En **sobrecompra (RSI > 70)**: Posible corrección a la baja
            - En **sobreventa (RSI < 30)**: Posible rebote alcista
            - **Divergencias** RSI/precio pueden anticipar cambios de tendencia
            """
        )

    def _render_no_data_message(self) -> None:
        st.warning(
            "No se pudieron obtener datos de los indicadores técnicos. "
            "Verifica que ALPHA_VANTAGE_API_KEY esté configurada."
        )
        self._render_no_data_help()

    def _render_combined_chart(
        self,
        hist: pd.DataFrame,
        sma_data: dict[int, dict[str, float] | None],
        rsi_data: dict[str, float],
        currency: str,
        interval: str,
    ) -> None:
        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.45, 0.25, 0.30],
        )

        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["Close"],
                mode="lines",
                name="Precio",
                line={"color": "#1f77b4", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(31,119,180,0.1)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f} "
                + currency
                + "<extra></extra>",
            ),
            row=1,
            col=1,
        )

        for period in self.SMA_PERIODS:
            data = sma_data.get(period)
            if data is None:
                continue
            sorted_dates = sorted(data.keys())
            values = [data[d] for d in sorted_dates]
            dates_pd = pd.to_datetime(sorted_dates)

            fig.add_trace(
                go.Scatter(
                    x=dates_pd,
                    y=values,
                    mode="lines",
                    name=f"SMA {period}",
                    line={
                        "color": self.SMA_COLORS[period],
                        "width": self.SMA_WIDTHS[period],
                    },
                    hovertemplate="%{x|%d %b %Y}<br>SMA "
                    + str(period)
                    + ": %{y:,.2f}<extra></extra>",
                ),
                row=1,
                col=1,
            )

        if "Volume" in hist.columns:
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist["Volume"],
                    name="Volumen",
                    marker_color="rgba(31,119,180,0.3)",
                    hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f}<extra></extra>",
                ),
                row=2,
                col=1,
            )

        rsi_dates = sorted(rsi_data.keys())
        rsi_values = [rsi_data[d] for d in rsi_dates]
        rsi_dates_pd = pd.to_datetime(rsi_dates)

        fig.add_trace(
            go.Scatter(
                x=rsi_dates_pd,
                y=rsi_values,
                mode="lines",
                name=f"RSI {self.RSI_PERIOD}",
                line={"color": "#9b59b6", "width": 1.5},
                fill="tozeroy",
                fillcolor="rgba(155,89,182,0.2)",
                hovertemplate="%{x|%d %b %Y}<br>RSI: %{y:.2f}<extra></extra>",
            ),
            row=3,
            col=1,
        )

        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="#d62728",
            row=3,
            col=1,
            annotation_text="70",
            annotation_position="bottom right",
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="#2ca02c",
            row=3,
            col=1,
            annotation_text="30",
            annotation_position="top right",
        )
        fig.add_hline(y=50, line_dash="dot", line_color="#999999", row=3, col=1)

        fig.update_layout(
            xaxis3={
                "rangeselector": {
                    "buttons": [
                        {"count": 1, "label": "1M", "step": "month"},
                        {"count": 3, "label": "3M", "step": "month"},
                        {"count": 6, "label": "6M", "step": "month"},
                        {
                            "count": 1,
                            "label": "YTD",
                            "step": "year",
                            "stepmode": "todate",
                        },
                        {"count": 1, "label": "1Y", "step": "year"},
                        {"label": "Todo", "step": "all"},
                    ]
                },
                "rangeslider": {"visible": True},
            },
            yaxis_title=f"Precio ({currency})",
            yaxis2_title="Volumen",
            yaxis3_title=f"RSI {self.RSI_PERIOD}",
            hovermode="x unified",
            height=700,
            margin={"l": 0, "r": 0, "t": 10, "b": 0},
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        fig.update_yaxes(range=[0, 100], row=3, col=1)

        st.plotly_chart(fig, width="stretch")

    def _render_combined_signals(
        self,
        hist: pd.DataFrame,
        sma_data: dict[int, dict[str, float] | None],
        rsi_data: dict[str, float],
    ) -> None:
        if hist.empty:
            return

        latest_price = hist["Close"].iloc[-1]

        sorted_dates_rsi = sorted(rsi_data.keys(), reverse=True)
        latest_rsi = rsi_data.get(sorted_dates_rsi[0], 0) if sorted_dates_rsi else 0
        prev_rsi = (
            rsi_data.get(sorted_dates_rsi[1], 0)
            if len(sorted_dates_rsi) > 1
            else latest_rsi
        )

        if latest_rsi > 70:
            rsi_signal = "🟠 Sobrecompra"
        elif latest_rsi < 30:
            rsi_signal = "🟢 Sobreventa"
        else:
            rsi_signal = "⚪ Neutral"

        rsi_delta = latest_rsi - prev_rsi if prev_rsi else 0

        metrics_cols = st.columns(len(self.SMA_PERIODS) + 2)
        with metrics_cols[0]:
            st.metric(
                "Precio",
                f"${latest_price:,.2f}" if latest_price > 0 else "N/A",
            )

        for i, period in enumerate(self.SMA_PERIODS):
            data = sma_data.get(period)
            if data is None:
                with metrics_cols[i + 1]:
                    st.metric(f"SMA {period}", "N/A")
                continue

            sorted_dates = sorted(data.keys(), reverse=True)
            if not sorted_dates:
                with metrics_cols[i + 1]:
                    st.metric(f"SMA {period}", "N/A")
                continue

            latest_sma = data.get(sorted_dates[0], 0)
            if latest_sma > 0:
                pct_diff = ((latest_price - latest_sma) / latest_sma) * 100
                signal = "▲" if pct_diff > 0 else "▼"
            else:
                pct_diff = 0
                signal = ""

            with metrics_cols[i + 1]:
                st.metric(
                    f"SMA {period}",
                    f"${latest_sma:,.2f}" if latest_sma > 0 else "N/A",
                    f"{signal}{abs(pct_diff):.2f}%" if latest_sma > 0 else None,
                )

        with metrics_cols[len(self.SMA_PERIODS) + 1]:
            st.metric(
                f"RSI {self.RSI_PERIOD}",
                f"{latest_rsi:.2f}",
                f"{rsi_delta:+.2f}" if rsi_delta else None,
            )

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**RSI:** {rsi_signal}")
        with col2:
            if latest_rsi > 70:
                st.markdown("⚠️ **Recomendación:** Precaución — zona de sobrecompra")
            elif latest_rsi < 30:
                st.markdown("✅ **Recomendación:** Oportunidad — zona de sobreventa")
            else:
                st.markdown("➡️ **Recomendación:** Neutral")

    def _render_no_data_help(self) -> None:
        st.markdown(
            """
            ### ¿Cómo obtener datos?

            Para usar los indicadores técnicos, necesitas configurar Alpha Vantage:

            1. Obtén una API key gratuita en [alphavantage.co](https://www.alphavantage.co/support/#api-key)
            2. Añade la siguiente línea a tu archivo `.env`:
            ```
            ALPHA_VANTAGE_API_KEY=tu_api_key_aqui
            ```
            3. Reinicia la aplicación

            **Límites del plan gratuito:**
            - 5 solicitudes por minuto
            - 25 solicitudes por día
            - Los datos se cachean automáticamente para minimizar uso
            """
        )
