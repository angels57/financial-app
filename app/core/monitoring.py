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
    if not dsn or dsn.strip() == "":
        logger.debug("Sentry DSN not configured, monitoring disabled")
        return

    if not _is_valid_dsn(dsn):
        logger.warning("Invalid Sentry DSN format, monitoring disabled")
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=0.1,
            send_default_pii=False,
            attach_stacktrace=True,
        )
        _initialized = True
        logger.info(f"Sentry monitoring initialized (env={environment})")
    except Exception:
        logger.warning("Failed to initialize Sentry, continuing without monitoring")


def _is_valid_dsn(dsn: str) -> bool:
    """Check if DSN has a valid Sentry format.

    Valid format: https://<public_key>@<host>/<project_id>
    """
    if not dsn or not isinstance(dsn, str):
        return False
    if not dsn.startswith("https://"):
        return False
    parts = dsn.replace("https://", "").split("@")
    if len(parts) != 2:
        return False
    return "/" in parts[1]
