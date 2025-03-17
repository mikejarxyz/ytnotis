import threading
from datetime import datetime, timezone

from src.youtube_api import fetch_youtube_video_data
from src.discord_notifier import send_discord_message
from src.database import store_video_id, was_posted, get_scheduled_videos
from src.logger import log_message
from src.config import DISCORD_NOTI_ROLE

def schedule_recheck(video_id, publish_at):
  """Schedules a recheck for a members-only video expected to go public."""
  try:
    publish_time = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))
    delay = max(0, (publish_time - datetime.now(timezone.utc)).total_seconds())

    if delay <= 0:
      log_message(f"⌛ Publish time for {video_id} is in the past. Checking immediately")
      recheck_video(video_id)
      return
    
    log_message(f"📅 Scheduling recheck for {video_id} in {delay} seconds (at {publish_time}).")

    # Run recheck in a separate thread to avoid blocking the main process
    threading.Timer(delay, recheck_video, args=[video_id]).start()

  except Exception as e:
    log_message(f"❌ Error scheduling recheck for {video_id}: {e}")

def recheck_video(video_id):
  """Checks if a scheduled members-only video has gone public and notifies Discord if so."""
  log_message(f"🔁 Rechecking video {video_id}")

  if was_posted(video_id):
    log_message(f"🏁 Video {video_id} was already posted; skipping.")
    return
  
  video_data = fetch_youtube_video_data(video_id)
  if not video_data:
    log_message(f"❌ Failed to fetch video data for {video_id}.")
    return
  
  if video_data["privacyStatus"] == "public":
    video_url = video_data["url"]
    video_title = video_data["title"]
    publish_at = video_data.get("publishAt") # Can be none

    if publish_at:
      publish_datetime = datetime.fromisoformat(publish_at.replace("Z", "+00:00"))

      if publish_datetime > datetime.now(tz=publish_datetime.tzinfo):
        log_message(f"🕒 Video {video_id} is scheduled for {publish_at}. Rechecking later.")
        schedule_recheck(video_id, publish_at)
        return
      
    discord_message = f"🎬 <@&{DISCORD_NOTI_ROLE}> New Video: {video_title}!\n🔗 {video_url}"

    if send_discord_message(discord_message):
      store_video_id(video_id, discord_posted=True)
      log_message(f'✅ Succesfully notified Discord about video with title: "{video_title}" and id: {video_id}.')
    else:
      log_message(f"🚨 Discord notification failed for {video_id}")

  else:
    log_message(f"❌ Video {video_id} is still not public.")

def resume_scheduled_tasks():
  """Resumes any scheduled video rechecks on bot restart."""
  log_message("🔎 Checking for scheduled videos to post later.")
  scheduled_videos = get_scheduled_videos()

  if not scheduled_videos:
    log_message("✅ No scheduled rechecks to resume.")
    return
  
  log_message(f"⏳ Resuming {len(scheduled_videos)} scheduled rechecks...")

  for video_id, publish_at in scheduled_videos:
    log_message(f"📅 Rescheduling recheck for video {video_id} at {publish_at}.")
    schedule_recheck(video_id, publish_at)