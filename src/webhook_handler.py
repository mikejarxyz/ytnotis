from flask import request, jsonify
from datetime import datetime
import xml.etree.ElementTree as ET

from src.token_manager import get_current_token
from src.database import is_video_in_db, store_video_id
from src.youtube_api import fetch_youtube_video_data
from src.discord_notifier import send_discord_message, should_notify
from src.video_rechecks import schedule_recheck
from src.logger import log_message
from src.config import DISCORD_NOTI_ROLE

def youtube_webhook():
    """Handles YouTube WebSub webhook."""

    token = get_current_token()

    # Handling the Google confirmation GET when subscribing
    if request.method == 'GET':
        hub_challenge = request.args.get("hub.challenge")
        if hub_challenge:
          return hub_challenge, 200
        else:
            return jsonify({"error": "Missing challenge token"}), 400
    
    # Checking to make sure the presented token matches
    if request.args.get("token") != token:
        log_message(f"🔒 Invalid token presented, aborting.")
        return jsonify({"error": "Invalid token"}), 403
    
    try:
        raw_data = request.data.decode("utf-8")
        log_message(f"🔔 Incoming Webhook Request:\nHeaders: {request.headers}\nQuery Params: {request.args}\nData:\n{raw_data}")
        
        try:
            root = ET.fromstring(raw_data)
            namespaces = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "at": "http://purl.org/atompub/tombstones/1.0"}
            
            # Do nothing if it's a Video Deleted notification
            if root.find(".//at:deleted-entry", namespaces):
                log_message("⚠️ Video Deletion. Ignoring.")
                return jsonify({"status": "ignored - deleted video"}), 200
            
            # Get the video ID and Published info
            video_id_elem = root.find(".//yt:videoId", namespaces)
            published_elem = root.find(".//atom:published", namespaces)
            
            video_id = video_id_elem.text if video_id_elem is not None else None
            published = published_elem.text if published_elem is not None else "Unknown"
            
            if not video_id:
                log_message("⚠️ No video ID Detected. Aborting.")
                return jsonify({"error": "No video ID found"}), 400
            
            log_message(f"📺 Received Video ID: {video_id}, Published: {published}")
            
            # Check to make sure the video is not stale (editting old content)
            if not should_notify(published):
                log_message(f"⌛ Published {published}, which is older than the threshold. Aborting")
                return jsonify({"status": "ignored - outdated video"}), 200
            
            # If the ID is already in the database, do nothing.
            if is_video_in_db(video_id):
                log_message(f"🔁 Video {video_id} already posted. Skipping.")
                return jsonify({"status": "ignored - duplicate video"}), 200
            
            # Getting the video data from YouTube API          
            video_data = fetch_youtube_video_data(video_id)
            if not video_data:
                log_message("❌ Failed to fetch YouTube data.")
                return jsonify({"error": "Failed to fetch video data"}), 500
            
            privacy_status = video_data.get("privacyStatus")
            publish_at = video_data.get("publishAt")
            live_broadcast = video_data.get("liveBroadcastContent")
            video_url = video_data.get("url")
            video_title = video_data.get("title")

            # Case 1: Upcoming Livestream
            if live_broadcast == "upcoming":
                log_message(f"🎥 Upcoming Livestream detected for {video_id}")

                scheduled_time_iso = video_data.get("scheduledStartTime")
                if scheduled_time_iso:
                    dt = datetime.fromisoformat(scheduled_time_iso.replace("Z", "+00:00"))
                    unix_timestamp = int(dt.timestamp())
                    scheduled_time = f"<t:{unix_timestamp}:R>"
                else:
                    scheduled_time = "is not known"

                discord_message = f"⭕ Livestream Scheduled!\nStarting {scheduled_time}!\n\n🔗 {video_url}"

                if send_discord_message(discord_message):
                    store_video_id(video_id, discord_posted=True)

                return jsonify({"status": "notified - upcoming livestream"}), 200
        
            # Case 2: Members-Only Video (Will be public later)
            if privacy_status == "public" and publish_at:
                log_message(f"🕒 Members-only video detected, scheduling recheck for {publish_at}")

                store_video_id(video_id, publish_at=publish_at, discord_posted=False)
                schedule_recheck(video_id, publish_at)

                return jsonify({"status": "scheduled - future public video"}), 200
            
            # Case 3: Instantly Public Video
            if privacy_status == "public" and not publish_at:
                log_message(f"✅ Public video detected: {video_id}")

                discord_message = f"🎬 <@&{DISCORD_NOTI_ROLE}> New Video: {video_title}!\n🔗 {video_url}"

                if send_discord_message(discord_message):
                    store_video_id(video_id, discord_posted=True)

                return jsonify({"status": "notified - public video"}), 200     
        
        except ET.ParseError:
            log_message("❌ XML Parse Error: Invalid Webhook Payload")
            return jsonify({"error": "Invalid XML"}), 400
    
    except Exception as e:
        log_message(f"❌ ERROR: {str(e)}")
        return jsonify({"error": "Server Error"}), 500

