"""Reusable loading utilities for Streamlit components."""

from __future__ import annotations

from typing import Callable, TypeVar

import streamlit as st

T = TypeVar("T")


def fetch_with_spinner(label: str, fn: Callable[[], T]) -> T:
    """Execute fn() showing an inline spinner. Returns the result."""
    with st.spinner(label):
        return fn()
