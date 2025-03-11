import logging
from logging.handlers import TimedRotatingFileHandler
from config import LOG_FILE

# Create a TimedRotatingFileHandler
handler = TimedRotatingFileHandler(
    LOG_FILE, when="D", interval=3, backupCount=3, encoding="utf-8"
)

# Set up logging format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

# Configure root logger
logger = logging.getLogger("YTWebhookLogger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

def log_message(message, level="info"):
    """Logs messages using the rotating logger."""
    level = level.lower()
    
    log_levels = {
        "debug": logger.debug,
        "warning": logger.warning,
        "error": logger.error,
        "critical": logger.critical,
    }
    
    log_levels.get(level, logger.info)(message)