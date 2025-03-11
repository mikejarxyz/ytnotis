import os
import time
import hashlib
import requests
from urllib.parse import quote

from src.config import TOKEN_ROTATION_PERIOD, LOCAL_WEBHOOK_URL, CHANNEL_ID
from src.logger import log_message

# Global variable to store the current token
CURRENT_TOKEN = None

def generate_new_token():
    """Generates a secure random token."""
    return hashlib.sha256(os.urandom(32)).hexdigest()[:32]

def get_current_token():
    """Returns the current WebSub token."""
    return CURRENT_TOKEN

def subscribe_websub(token):
    """Subscribes YouTube WebSub with the given token."""
    callback_url = f"{LOCAL_WEBHOOK_URL}/webhook?token={quote(token)}"
    log_message("Attempting to subscribe to WebSub...")
    
    response = requests.post("https://pubsubhubbub.appspot.com/subscribe", data={
        "hub.mode": "subscribe",
        "hub.topic": f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={CHANNEL_ID}",
        "hub.callback": callback_url
    })
    
    log_message(f"🔔 WebSub Subscription Response: {response.status_code} {response.text}")

def unsubscribe_websub(token):
    """Unsubscribes from YouTube WebSub to prevent duplicate notifications."""
    callback_url = f"{LOCAL_WEBHOOK_URL}/webhook?token={quote(token)}"
    log_message("Attempting to unsubscribe from WebSub...")
    
    response = requests.post("https://pubsubhubbub.appspot.com/subscribe", data={
        "hub.mode": "unsubscribe",
        "hub.topic": f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={CHANNEL_ID}",
        "hub.callback": callback_url
    })
    
    log_message(f"🔕 WebSub Unsubscription Response: {response.status_code} {response.text}")

def rotate_token():
    """Rotates the token immediately on startup and then every rotation period."""
    global CURRENT_TOKEN
    
    while True:
        if CURRENT_TOKEN is not None:
            unsubscribe_websub(CURRENT_TOKEN)
        
        CURRENT_TOKEN = generate_new_token()
        subscribe_websub(CURRENT_TOKEN)
        log_message("🔄 Token rotated")
        
        time.sleep(TOKEN_ROTATION_PERIOD)  # Sleep until next rotation