import threading
from flask import Flask
from src.token_manager import rotate_token
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

if __name__ == "__main__":
  log_message("🚀 Starting YouTube Webhook Server...")

  # Resume any scheduled rechecks from the database
  resume_scheduled_tasks()

  # Start token rotation as a background task
  start_token_rotation()
  
  app.run(host=HOST, port=PORT)