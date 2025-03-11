import datetime
from datetime import datetime, timedelta
from config import DISCORD_NOTI_ROLE

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