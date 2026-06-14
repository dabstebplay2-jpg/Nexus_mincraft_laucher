import logging
import os

from core.logger import redact_secret

logger = logging.getLogger(__name__)


PROXY_ENV_KEYS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]


def log_proxy_environment():
    found_proxy = False

    for key in PROXY_ENV_KEYS:
        value = os.environ.get(key)

        if value:
            found_proxy = True
            logger.warning("Proxy env detected: %s=%s", key, redact_secret(value))

    if not found_proxy:
        logger.info("No proxy environment variables detected")


def disable_proxy_for_launcher():
    logger.info("Disabling proxy environment variables for launcher process")

    for key in PROXY_ENV_KEYS:
        value = os.environ.pop(key, None)

        if value:
            logger.warning("Removed proxy env: %s=%s", key, redact_secret(value))

    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"

    logger.info("NO_PROXY set to *")