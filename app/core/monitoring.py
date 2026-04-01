import sentry_sdk

from .logging import get_app_logger

logger = get_app_logger("Monitoring")

_initialized = False


def init_monitoring(dsn: str | None = None, environment: str = "development") -> None:
    """Initialize Sentry monitoring.

    No-op if dsn is None or empty — safe to call always.

    Args:
        dsn: Sentry DSN string from settings or env.
        environment: Environment tag (development, production, etc.).
    """
    global _initialized
    if _initialized:
        return
    if not dsn:
        logger.debug("Sentry DSN not configured, monitoring disabled")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        traces_sample_rate=0.1,  # 10% of transactions
        send_default_pii=False,  # No enviar datos personaless
        attach_stacktrace=True,  # Stack trace en todos los eventos
    )
    _initialized = True
    logger.info(f"Sentry monitoring initialized (env={environment})")
