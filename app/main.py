import streamlit as st

from core import get_app_logger, init_monitoring
from settings import settings

logger = get_app_logger("")


def main():
    init_monitoring(dsn=settings.sentry_dsn, environment=settings.environment)
    logger.info("Hello World")
    st.title("Financial Stre")


if __name__ == "__main__":
    main()
