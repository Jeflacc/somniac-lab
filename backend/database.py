import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def auto_migrate():
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_agents'")
        if not cursor.fetchone():
            return
            
        columns = [info[1] for info in cursor.execute("PRAGMA table_info(ai_agents)").fetchall()]
        if "discord_token" not in columns:
            cursor.execute("ALTER TABLE ai_agents ADD COLUMN discord_token VARCHAR DEFAULT ''")
        if "discord_channel_id" not in columns:
            cursor.execute("ALTER TABLE ai_agents ADD COLUMN discord_channel_id VARCHAR DEFAULT ''")
        if "discord_connected" not in columns:
            cursor.execute("ALTER TABLE ai_agents ADD COLUMN discord_connected BOOLEAN DEFAULT 0")
        if "profile_picture" not in columns:
            cursor.execute("ALTER TABLE ai_agents ADD COLUMN profile_picture VARCHAR")
        if "banner_picture" not in columns:
            cursor.execute("ALTER TABLE ai_agents ADD COLUMN banner_picture VARCHAR")
            
        conn.commit()
    except Exception as e:
        print(f"Auto-migration error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

auto_migrate()
