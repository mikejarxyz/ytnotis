import threading
import signal
import sys
from flask import Flask
from src.token_manager import rotate_token, unsubscribe_websub, get_current_token
from src.webhook_handler import youtube_webhook
from src.video_rechecks import resume_scheduled_tasks
from src.config import HOST, PORT
from src.logger import log_message

app = Flask(__name__)

# Register the webhook route
app.add_url_rule('/webhook', 'youtube_webhook', youtube_webhook, methods=['GET', 'POST'])

def start_token_rotation():
  """Starts the token rotation in a separate thread."""
  token_thread = threading.Thread(target=rotate_token, daemon=True)
  token_thread.start()

def graceful_shutdown(signal_received, frame):
    """Handles shutdown signal (SIGTERM) and unsubscribes before exiting."""
    log_message("⚠️ Received termination signal. Unsubscribing from WebSub...")

    current_token = get_current_token()
    if current_token:
        unsubscribe_websub(current_token)
        log_message("✅ Successfully unsubscribed from WebSub.")
    
    log_message("🔻 Shutting down gracefully.")
    sys.exit(0)  # Exit the script cleanly

# Register signal handler for graceful shutdown
signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)  # Handle Ctrl+C for local testing

if __name__ == "__main__":
  log_message("🚀 Starting YouTube Webhook Server...")

  # Resume any scheduled rechecks from the database
  resume_scheduled_tasks()

  # Start token rotation as a background task
  start_token_rotation()
  
  app.run(host=HOST, port=PORT)