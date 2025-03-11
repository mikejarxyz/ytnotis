import os
import logging
from logging.handlers import TimedRotatingFileHandler

# Set the Log Dir / filename
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "ytnotis.log")

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