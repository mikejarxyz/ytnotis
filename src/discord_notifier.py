import time
import requests
from datetime import datetime, timedelta

from src.config import DISCORD_WEBHOOK_URL, DISCORD_NOTI_ROLE
from src.logger import log_message

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

def generate_discord_message(video_data):
    """Determines the appropriate Discord message based on video type."""
    
    if video_data["liveBroadcastContent"] == "upcoming":
        scheduled_time_iso = video_data.get("scheduledStartTime")
        if scheduled_time_iso:
            dt = datetime.fromisoformat(scheduled_time_iso.replace("Z", "+00:00"))
            unix_timestamp = int(dt.timestamp())
            scheduled_time = f"<t:{unix_timestamp}:R>"
        else:
            scheduled_time = "Unknown Time"
        
        return f"⭕ Livestream Scheduled!\nStarting {scheduled_time}!\n\n🔗 {video_data['url']}"
    
    if video_data["liveBroadcastContent"] == "live":
        return None  # Ignoring currently live streams
    
    if "liveStreamingDetails" in video_data:
        return None  # Ignoring finished livestreams
    
    return f"🎬 <@&{DISCORD_NOTI_ROLE}> New Video: {video_data['title']}!\n🔗 {video_data['url']}"

def should_notify(published_date_str, days_threshold=7):
    """Returns True if the video was published within the last `days_threshold` days."""
    published_date = datetime.strptime(published_date_str, "%Y-%m-%dT%H:%M:%S%z")
    current_time = datetime.now(tz=published_date.tzinfo)  # Keep timezone consistent
    return (current_time - published_date) < timedelta(days=days_threshold)