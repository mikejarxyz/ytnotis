import os
from dotenv import load_dotenv

from src.logger import log_message

load_dotenv()

#########################   CONFIG START   ##################################

# Token Rotation
TOKEN_ROTATION_PERIOD = 172800 # 2-day (in seconds) secret token rotation

# Server Config
HOST = "0.0.0.0"
PORT = 5069

#########################   CONFIG END   ####################################

# Set up the directories for data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "yt_video_ids.db")

# Get VARS from .env
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DISCORD_NOTI_ROLE = os.getenv("DISCORD_NOTI_ROLE")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
LOCAL_WEBHOOK_URL = os.getenv("LOCAL_WEBHOOK_URL")

# Validation to ensure required environment variables exist
missing_vars = []
if not CHANNEL_ID:
    missing_vars.append("CHANNEL_ID")
if not YOUTUBE_API_KEY:
    missing_vars.append("YOUTUBE_API_KEY")
if not DISCORD_NOTI_ROLE:
    missing_vars.append("VIDEO_NOTIS_ROLE_ID")
if not DISCORD_WEBHOOK_URL:
    missing_vars.append("DISCORD_WEBHOOK_URL")
if not LOCAL_WEBHOOK_URL:
    missing_vars.append("LOCAL_WEBHOOK_URL")

if missing_vars:
    error_message = f"❌ Missing required environment variables: {', '.join(missing_vars)}"
    log_message(error_message)  # Log the error to the file
    raise ValueError(error_message)  # Then raise the error to stop execution
