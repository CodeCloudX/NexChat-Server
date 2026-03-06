import logging
import sys
from app.core.config import settings

def setup_logging():
    """
    Configures centralized logging for the application.
    """
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silent noisy libraries (only show warnings/errors)
    # We remove uvicorn.access from here to see API hits in the console
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
