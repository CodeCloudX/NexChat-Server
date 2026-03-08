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
        
        # Capture and suppress python warnings
        logging.captureWarnings(True)
        logging.getLogger("py.warnings").setLevel(logging.CRITICAL)
        
        # Also silence specific noisy loggers completely
        noisy_loggers = [
            "uvicorn", "uvicorn.access", "uvicorn.error", 
            "fastapi", "sqlalchemy.engine", "httpx", 
            "httpcore", "firebase_admin", "passlib"
        ]
        for logger_name in noisy_loggers:
            l = logging.getLogger(logger_name)
            l.setLevel(logging.CRITICAL)
            l.propagate = False
    else:
        # Standard silent noisy libraries for development
        # We still keep these at WARNING to avoid terminal spam
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("firebase_admin").setLevel(logging.WARNING)
