from flask import Blueprint, request, jsonify
import xml.etree.ElementTree as ET

from src.database import is_video_in_db, store_video_id
from src.youtube_api import fetch_youtube_video_data
from src.discord_notifier import send_discord_message
from src.logger import log_message
from src.utils import generate_discord_message, should_notify
from src.token_manager import get_current_token

def youtube_webhook():
    """Handles YouTube WebSub webhook."""

    token = get_current_token()

    if request.method == 'GET':
        hub_challenge = request.args.get("hub.challenge")
        if hub_challenge:
          return hub_challenge, 200
        else:
            return jsonify({"error": "Missing challenge token"}), 400
    
    if request.args.get("token") != token:
        log_message(f"🔒 Invalid token presented, aborting.")
        return jsonify({"error": "Invalid token"}), 403
    
    try:
        raw_data = request.data.decode("utf-8")
        log_message(f"🔔 Incoming Webhook Request:\nHeaders: {request.headers}\nQuery Params: {request.args}\nData:\n{raw_data}")
        
        try:
            root = ET.fromstring(raw_data)
            namespaces = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "at": "http://purl.org/atompub/tombstones/1.0"}
            
            if root.find(".//at:deleted-entry", namespaces):
                log_message("⚠️ Video Deletion. Ignoring.")
                return jsonify({"status": "ignored - deleted video"}), 200
            
            video_id_elem = root.find(".//yt:videoId", namespaces)
            published_elem = root.find(".//atom:published", namespaces)
            
            video_id = video_id_elem.text if video_id_elem is not None else None
            published = published_elem.text if published_elem is not None else "Unknown"
            
            if not video_id:
                log_message("⚠️ No video ID Detected. Aborting.")
                return jsonify({"error": "No video ID found"}), 400
            
            log_message(f"📺 Received Video ID: {video_id}, Published: {published}")
            
            if not should_notify(published):
                log_message(f"⌛ Published {published}, which is older than the threshold. Aborting")
                return jsonify({"status": "ignored - outdated video"}), 200
            
            if is_video_in_db(video_id):
                log_message(f"🔁 Video {video_id} already posted. Skipping.")
                return jsonify({"status": "ignored - duplicate video"}), 200
            
            video_data = fetch_youtube_video_data(video_id)
            if not video_data:
                log_message("❌ Failed to fetch YouTube data.")
                return jsonify({"error": "Failed to fetch video data"}), 500
            
            discord_message = generate_discord_message(video_data)
            if not discord_message:
                return jsonify({"status": "ignored - not a new video"}), 200
        
        except ET.ParseError:
            log_message("❌ XML Parse Error: Invalid Webhook Payload")
            return jsonify({"error": "Invalid XML"}), 400
        
        if send_discord_message(discord_message):
            store_video_id(video_id)
        else:
            log_message("🚨 Discord post failed, NOT storing video ID.")
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        log_message(f"❌ ERROR: {str(e)}")
        return jsonify({"error": "Server Error"}), 500

