import requests
from logger import log_message
from config import YOUTUBE_API_KEY

def fetch_youtube_video_data(video_id):
    """Call YouTube API to determine if it's a video or livestream."""
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,liveStreamingDetails&id={video_id}&key={YOUTUBE_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for non-200 responses
        data = response.json()
        
        if "items" not in data or not data["items"]:
            log_message(f"⚠️ No data found for video ID: {video_id}")
            return None
        
        video = data["items"][0]
        return {
            "title": video["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "liveBroadcastContent": video["snippet"].get("liveBroadcastContent", "none"),
            "scheduledStartTime": video.get("liveStreamingDetails", {}).get("scheduledStartTime"),
        }
    
    except requests.exceptions.RequestException as e:
        log_message(f"❌ YouTube API Error: {e}", level="error")
        return None