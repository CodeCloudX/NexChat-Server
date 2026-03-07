import logging
import sys
import os
from app.core.config import settings

def setup_logging():
    """
    Configures centralized logging for the application.
    If ENV is 'production', it silences all logs except critical errors and disables print.
    """
    is_prod = settings.ENV == "production"

    # In production, we set the level to CRITICAL to stop almost all logs
    log_level = logging.CRITICAL if is_prod else settings.LOG_LEVEL

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # If production, override the builtin print to do nothing
    if is_prod:
        import builtins
        # This effectively disables 'print()' across the entire app
        builtins.print = lambda *args, **kwargs: None

        # Also silence specific noisy loggers completely
        for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "sqlalchemy.engine", "httpx"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
            logging.getLogger(logger_name).propagate = False
    else:
        # Standard silent noisy libraries for development
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
