"""Componentes UI reutilizables para el dashboard."""

import streamlit as st


def render_diff_badge(diff: float, label: str = "vs precio actual") -> None:
    """
    Renderiza una etiqueta de diferencia con colores.

    Verde: diff < 0 (precio por debajo del fair value = oportunidad)
    Rojo: diff > 0 (precio por encima del fair value = sobrevalorado)

    Args:
        diff: Porcentaje de diferencia
        label: Etiqueta a mostrar (default: "vs precio actual")
    """
    color = "green" if diff < 0 else "red"
    st.markdown(
        f'<span style="color:{color}; font-size:0.9em;">{label}: {diff:+.1f}%</span>',
        unsafe_allow_html=True,
    )
