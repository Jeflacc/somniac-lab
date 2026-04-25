import sqlite3
import os

db_path = "app.db"

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Adding email column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
        conn.close()
        print("Successfully added email column!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column 'email' already exists.")
        else:
            print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
else:
    print(f"Database file {db_path} not found.")
