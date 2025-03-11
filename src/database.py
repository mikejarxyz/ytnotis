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
                published TEXT
            )
            """
        )
        conn.commit()
        conn.close()
        log_message("📂 Database initialized successfully.")
    except sqlite3.Error as e:
        log_message(f"❌ Database initialization failed: {e}", level="error")

def store_video_id(video_id: str, published: str = None):
    """Insert video ID and published timestamp into the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (video_id, published) VALUES (?, ?)", (video_id, published))
        conn.commit()
        log_message(f"💽 Video stored in Database with ID: {video_id}")
    except sqlite3.IntegrityError:
        log_message(f"⚠️ Video ID {video_id} already exists in the database.", level="warning")
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

# Ensure the database is set up when the script runs
initialize_database()