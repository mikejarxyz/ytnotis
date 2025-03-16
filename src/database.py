import sqlite3

from src.config import DB_FILE
from src.logger import log_message

def initialize_database():
    """Creates the database and videos table if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                publishAt TEXT,
                discordPosted BOOLEAN DEFAULT 0
            )
            """
        )
        conn.commit()
        conn.close()
        log_message("📂 Database initialized successfully.")
    except sqlite3.Error as e:
        log_message(f"❌ Database initialization failed: {e}", level="error")

def store_video_id(video_id: str, publish_at: str = None, discord_posted: bool = False):
    """Insert or update video entry in the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO videos (video_id, publishAt, discordPosted)
            VALUES (?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                publishAt = excluded.publishAt,
                discordPosted = excluded.discordPosted
            """,
            (video_id, publish_at, int(discord_posted))
        )
        conn.commit()
        log_message(f"💽 Video stored: ID={video_id}, publishAt={publish_at}, discordPosted={discord_posted}")
    except sqlite3.Error as e:
        log_message(f"❌ Database error while storing video ID {video_id}: {e}", level="error")
    finally:
        conn.close()

def is_video_in_db(video_id: str) -> bool:
    """Check if the video ID already exists in the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()
        return bool(result)
    except sqlite3.Error as e:
        log_message(f"❌ Database error while checking video ID {video_id}: {e}", level="error")
        return False
    finally:
        conn.close()

def was_posted(video_id: str) -> bool:
    """Check if the video has already been posted to Discord."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT discordPosted FROM videos WHERE video_id = ?", (video_id,))
        result = cursor.fetchone()
        return bool(result and result[0])
    except sqlite3.Error as e:
        log_message(f"❌ Database error while checking if video {video_id} was posted: {e}", level="error")
        return False
    finally:
        conn.close()

def get_scheduled_videos():
    """Retrieve videos that need rechecking (have publishAt but no discordPosted)."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT video_id, publishAt FROM videos WHERE publishAt IS NOT NULL AND discordPosted = 0")
        videos = cursor.fetchall()
        return videos
    except sqlite3.Error as e:
        log_message(f"❌ Database error while fetching scheduled videos: {e}", level="error")
        return []
    finally:
        conn.close()

# Ensure the database is set up when the script runs
initialize_database()