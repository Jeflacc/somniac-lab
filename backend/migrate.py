import sqlite3
import os

db_path = 'somniac.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check and add columns to users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN inventory JSON DEFAULT '[]'")
        print("Added inventory to users.")
    except sqlite3.OperationalError:
        print("inventory column already exists.")

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN timezone VARCHAR DEFAULT 'Asia/Jakarta'")
        print("Added timezone to users.")
    except sqlite3.OperationalError:
        print("timezone column already exists.")
        
    # Check and add columns to ai_agents
    try:
        cursor.execute("ALTER TABLE ai_agents ADD COLUMN banner_picture VARCHAR")
        print("Added banner_picture to ai_agents.")
    except sqlite3.OperationalError:
        print("banner_picture column already exists.")
        
    conn.commit()
    conn.close()
    print("Migration complete.")
else:
    print("Database not found, maybe it has a different name or path.")
