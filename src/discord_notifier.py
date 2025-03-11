import time
import requests
from config import DISCORD_WEBHOOK_URL
from logger import log_message

def send_discord_message(message: str, retries: int = 3) -> bool:
    """Sends a message to Discord, with retries on failure."""
    payload = {"content": message}
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(retries):
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
        
        if response.status_code == 204:  # Success
            log_message("✅ Discord Message Sent Successfully")
            return True
        
        log_message(f"⚠️ Discord Response ({response.status_code}): {response.text}")
        
        if response.status_code == 429:  # Rate-limited
            retry_after = response.json().get("retry_after", 2000) / 1000  # Convert ms → seconds
            log_message(f"⏳ Rate-limited! Retrying in {retry_after} seconds...")
            time.sleep(retry_after)
        else:
            time.sleep(2)  # Small delay before retrying
    
    log_message("❌ Failed to send Discord message after retries.")
    return False