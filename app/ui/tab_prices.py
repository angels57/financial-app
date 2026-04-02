"""Tab de cálculo de precios de compra y futuros."""

import streamlit as st

from models import StockInfo
from scrapers.guru_focus_scraper import GuruFocusScraper
from ui.base_tab import BaseTab


class PricesTab(BaseTab):
    """Calcula precios de compra y futuros según múltiplos financieros."""

    def render(self, *, info: StockInfo, **kwargs) -> None:
        t = info.ticker
        (
            per_default,
            ps_default,
            pfcf_default,
            beneficios_default,
            ventas_default,
            fcf_default,
        ) = self._render_inputs(info, t)
        buy_prices = self._render_buy_prices(
            per_default,
            ps_default,
            pfcf_default,
            beneficios_default,
            ventas_default,
            fcf_default,
            info,
            t,
        )

        st.markdown("---")
        future_avg = self._render_future_prices(
            per_default, ps_default, pfcf_default, info, t
        )

        st.markdown("---")
        self._render_returns(info.price, future_avg, info.dividend_yield, t)

        st.markdown("---")
        self._render_fair_value_comparison(buy_prices, info.price, t)

    def _render_inputs(self, info: StockInfo, t: str) -> tuple:
        per_default = float(info.pe_ratio or 0)
        ps_default = float(info.price_to_sales or 0)
        pfcf_default = float(info.price_to_fcf or 0)
        beneficios_default = float((info.net_income or 0) / 1e6)
        ventas_default = float((info.total_revenue or 0) / 1e6)
        fcf_default = float((info.free_cash_flow or 0) / 1e6)

        return (
            per_default,
            ps_default,
            pfcf_default,
            beneficios_default,
            ventas_default,
            fcf_default,
        )

    def _render_buy_prices(
        self,
        per_default: float,
        ps_default: float,
        pfcf_default: float,
        beneficios_default: float,
        ventas_default: float,
        fcf_default: float,
        info: StockInfo,
        t: str,
    ) -> float:
        st.subheader("Precios de Compra según Ratios")

        shares_default = float((info.shares_outstanding or 0) / 1e6)
        shares = st.number_input(
            "Acciones en circulación (M)",
            value=shares_default,
            min_value=0.0,
            format="%.2f",
            key=f"shares_{t}",
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            with st.container(border=True):
                st.markdown("**SEGÚN PER**")
                per = st.number_input(
                    "PER promedio",
                    value=per_default,
                    min_value=0.0,
                    format="%.2f",
                    key=f"per_{t}",
                )
                beneficios = st.number_input(
                    "Beneficios (M)",
                    value=beneficios_default,
                    format="%.2f",
                    key=f"beneficios_{t}",
                )
                precio_per = (
                    (beneficios / shares) * per if shares > 0 and per > 0 else 0
                )
                st.metric("Precio", f"${precio_per:,.1f}" if precio_per else "N/A")
                st.markdown("---")
                st.latex(
                    r"\frac{\text{Beneficios}}{\text{Acciones}} \times \text{PER promedio}"
                )
                st.caption(
                    f"({beneficios:.2f}M / {shares:.2f}M) × {per:.2f} = ${precio_per:,.2f}"
                )

        with col2:
            with st.container(border=True):
                st.markdown("**SEGÚN VENTAS**")
                ps = st.number_input(
                    "P/S promedio",
                    value=ps_default,
                    min_value=0.0,
                    format="%.2f",
                    key=f"ps_{t}",
                )
                ventas = st.number_input(
                    "Ventas (M)",
                    value=ventas_default,
                    min_value=0.0,
                    format="%.2f",
                    key=f"ventas_{t}",
                )
                precio_ps = (ventas / shares) * ps if shares > 0 and ps > 0 else 0
                st.metric("Precio", f"${precio_ps:,.1f}" if precio_ps else "N/A")
                st.markdown("---")
                st.latex(
                    r"\frac{\text{Ventas}}{\text{Acciones}} \times \text{P/S promedio}"
                )
                st.caption(
                    f"({ventas:.2f}M / {shares:.2f}M) × {ps:.2f} = ${precio_ps:,.2f}"
                )

        with col3:
            with st.container(border=True):
                st.markdown("**SEGÚN FCF**")
                pfcf = st.number_input(
                    "P/FCF promedio",
                    value=pfcf_default,
                    min_value=0.0,
                    format="%.2f",
                    key=f"pfcf_{t}",
                )
                fcf = st.number_input(
                    "Flujo de Caja (M)",
                    value=fcf_default,
                    format="%.2f",
                    key=f"fcf_{t}",
                )
                precio_fcf = (fcf / shares) * pfcf if shares > 0 and pfcf > 0 else 0
                st.metric("Precio", f"${precio_fcf:,.1f}" if precio_fcf else "N/A")
                st.markdown("---")
                st.latex(
                    r"\frac{\text{FCF}}{\text{Acciones}} \times \text{P/FCF promedio}"
                )
                st.caption(
                    f"({fcf:.2f}M / {shares:.2f}M) × {pfcf:.2f} = ${precio_fcf:,.2f}"
                )

        with col4:
            with st.container(border=True):
                st.markdown("**PROMEDIO**")
                precios = [p for p in [precio_per, precio_ps, precio_fcf] if p > 0]
                promedio = sum(precios) / len(precios) if precios else 0
                st.metric("Precio", f"${promedio:,.1f}" if promedio else "N/A")
                st.markdown("---")
                st.latex(r"\frac{\text{PER} + \text{P/S} + \text{P/FCF}}{3}")
                precios_calc = [p for p in [precio_per, precio_ps, precio_fcf] if p > 0]
                promedio_calc = (
                    sum(precios_calc) / len(precios_calc) if precios_calc else 0
                )
                st.caption(
                    f"(${precio_per:,.2f} + ${precio_ps:,.2f} + ${precio_fcf:,.2f}) / 3 = ${promedio_calc:,.2f}"
                )

        return promedio

    def _render_future_prices(
        self,
        per_default: float,
        ps_default: float,
        pfcf_default: float,
        info: StockInfo,
        t: str = "",
    ) -> float:
        @st.fragment
        def _fragment():
            st.subheader("Precios Futuros (Proyección)")

            shares = st.session_state.get(f"shares_{t}", 0.0)
            per = st.session_state.get(f"per_{t}", per_default)
            ps = st.session_state.get(f"ps_{t}", ps_default)
            pfcf = st.session_state.get(f"pfcf_{t}", pfcf_default)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                with st.container(border=True):
                    st.markdown("**SEGÚN EPS**")
                    ben_futuro = st.number_input(
                        "Beneficios futuros (M)",
                        value=0.0,
                        format="%.2f",
                        key=f"ben_futuro_{t}",
                    )
                    precio_eps = (
                        (ben_futuro / shares) * per if shares > 0 and per > 0 else 0
                    )
                    st.metric("Precio", f"${precio_eps:,.1f}" if precio_eps else "N/A")
                    st.markdown("---")
                    st.latex(
                        r"\frac{\text{Ben. fut.}}{\text{Acciones}} \times \text{PER}"
                    )
                    st.caption(
                        f"({ben_futuro:.2f}M / {shares:.2f}M) × {per:.2f} = ${precio_eps:,.2f}"
                    )

            with col2:
                with st.container(border=True):
                    st.markdown("**SEGÚN VENTAS**")
                    ventas_futuro = st.number_input(
                        "Ventas futuras (M)",
                        value=0.0,
                        min_value=0.0,
                        format="%.2f",
                        key=f"ventas_futuro_{t}",
                    )
                    precio_ventas = (
                        (ventas_futuro / shares) * ps if shares > 0 and ps > 0 else 0
                    )
                    st.metric(
                        "Precio",
                        f"${precio_ventas:,.1f}" if precio_ventas else "N/A",
                    )
                    st.markdown("---")
                    st.latex(
                        r"\frac{\text{Ventas fut.}}{\text{Acciones}} \times \text{P/S}"
                    )
                    st.caption(
                        f"({ventas_futuro:.2f}M / {shares:.2f}M) × {ps:.2f} = ${precio_ventas:,.2f}"
                    )

            with col3:
                with st.container(border=True):
                    st.markdown("**SEGÚN FCF**")
                    fcf_futuro = st.number_input(
                        "Flujo de Caja futuro (M)",
                        value=0.0,
                        format="%.2f",
                        key=f"fcf_futuro_{t}",
                    )
                    precio_fcf = (
                        (fcf_futuro / shares) * pfcf if shares > 0 and pfcf > 0 else 0
                    )
                    st.metric("Precio", f"${precio_fcf:,.1f}" if precio_fcf else "N/A")
                    st.markdown("---")
                    st.latex(
                        r"\frac{\text{FCF fut.}}{\text{Acciones}} \times \text{P/FCF}"
                    )
                    st.caption(
                        f"({fcf_futuro:.2f}M / {shares:.2f}M) × {pfcf:.2f} = ${precio_fcf:,.2f}"
                    )

            with col4:
                with st.container(border=True):
                    st.markdown("**PROMEDIO**")
                    precios = [
                        p for p in [precio_eps, precio_ventas, precio_fcf] if p > 0
                    ]
                    promedio = sum(precios) / len(precios) if precios else 0
                    st.metric("Precio", f"${promedio:,.1f}" if promedio else "N/A")
                    st.markdown("---")
                    st.latex(r"\frac{\text{EPS} + \text{Ventas} + \text{FCF}}{3}")
                    st.caption(
                        f"(${precio_eps:,.2f} + ${precio_ventas:,.2f} + ${precio_fcf:,.2f}) / 3 = ${promedio:,.2f}"
                    )

            st.session_state[f"future_avg_{t}"] = promedio

        _fragment()
        return st.session_state.get(f"future_avg_{t}", 0.0)

    def _render_returns(
        self,
        precio_compra: float,
        precio_futuro: float,
        dividend_yield: float | None,
        t: str = "",
    ) -> None:
        @st.fragment
        def _fragment():
            st.subheader("Rentabilidad Esperada")
            future_avg = st.session_state.get(f"future_avg_{t}", precio_futuro)

            col1, col2 = st.columns(2)
            with col1:
                horizonte = st.slider(
                    "Horizonte de inversión (años)",
                    min_value=1,
                    max_value=10,
                    value=5,
                    key=f"horizonte_{t}",
                )
            with col2:
                div_yield = st.number_input(
                    "Dividend Yield (%)",
                    value=float((dividend_yield or 0) * 100),
                    min_value=0.0,
                    format="%.2f",
                    key=f"div_yield_{t}",
                )

            if precio_compra > 0 and future_avg > 0:
                rentabilidad = ((future_avg - precio_compra) / precio_compra) * 100
                r_anualizada = ((1 + rentabilidad / 100) ** (1 / horizonte) - 1) * 100
                retorno_total = r_anualizada + div_yield

                c1, c2, c3 = st.columns(3)
                c1.metric("Rentabilidad Total", f"{rentabilidad:,.2f}%")
                c2.metric("R. Anualizada", f"{r_anualizada:,.2f}%", f"{horizonte} años")
                c3.metric(
                    "Retorno Total",
                    f"{retorno_total:,.2f}%",
                    f"+{div_yield:.2f}% div",
                )
            else:
                st.info(
                    "Ingresa datos de precios futuros para calcular la rentabilidad."
                )

        _fragment()

    def _render_fair_value_comparison(
        self, precio_promedio: float, precio_actual: float, t: str = ""
    ) -> None:
        @st.fragment
        def _fragment():
            st.subheader("Comparación con Fair Values Externos")
            if t:
                st.link_button(
                    "📊 Ver en InvestingPro",
                    f"https://www.investing.com/pro/{t.lower()}",
                    width="content",
                )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                with st.container(border=True):
                    st.markdown("**MI CÁLCULO**")
                    st.metric(
                        "Fair Value",
                        f"${precio_promedio:,.1f}" if precio_promedio else "N/A",
                    )
                    if precio_promedio > 0 and precio_actual > 0:
                        diff = (
                            (precio_actual - precio_promedio) / precio_promedio
                        ) * 100
                        st.markdown("---")
                        st.caption(f"vs precio actual: {diff:+.1f}%")

            with col2:
                with st.container(border=True):
                    st.markdown("**INVESTINGPRO**")
                    fv_investing = st.number_input(
                        "Fair Value",
                        value=0.0,
                        min_value=0.0,
                        format="%.2f",
                        key=f"fv_investing_{t}",
                    )
                    st.metric(
                        "Precio",
                        f"${fv_investing:,.1f}" if fv_investing else "N/A",
                    )
                    if fv_investing > 0 and precio_actual > 0:
                        diff_inv = ((precio_actual - fv_investing) / fv_investing) * 100
                        st.markdown("---")
                        st.caption(f"vs precio actual: {diff_inv:+.1f}%")

            with col3:
                with st.container(border=True):
                    st.markdown("**GURUFOCUS**")
                    fv_guru_default = st.session_state.get(f"fv_guru_{t}", None)
                    if fv_guru_default is None:
                        with st.spinner("Cargando GF Value..."):
                            scraper = GuruFocusScraper(headless=True)
                            fv_guru_default = scraper.get_fair_value(t) or 0.0
                    fv_guru = st.number_input(
                        "Fair Value",
                        value=fv_guru_default,
                        min_value=0.0,
                        format="%.2f",
                        key=f"fv_guru_{t}",
                    )
                    st.metric(
                        "Precio",
                        f"${fv_guru:,.1f}" if fv_guru else "N/A",
                    )
                    if fv_guru > 0 and precio_actual > 0:
                        diff_guru = ((precio_actual - fv_guru) / fv_guru) * 100
                        st.markdown("---")
                        st.caption(f"vs precio actual: {diff_guru:+.1f}%")

            with col4:
                with st.container(border=True):
                    st.markdown("**ALPHASPREAD**")
                    fv_alpha = st.number_input(
                        "Fair Value",
                        value=0.0,
                        min_value=0.0,
                        format="%.2f",
                        key=f"fv_alpha_{t}",
                    )
                    st.metric(
                        "Precio",
                        f"${fv_alpha:,.1f}" if fv_alpha else "N/A",
                    )
                    if fv_alpha > 0 and precio_actual > 0:
                        diff_alpha = ((precio_actual - fv_alpha) / fv_alpha) * 100
                        st.markdown("---")
                        st.caption(f"vs precio actual: {diff_alpha:+.1f}%")

        _fragment()
