import sqlite3
import os
import chromadb

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

def migrate():
    print("Starting multi-tenant migration...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Rename ai_instances to ai_agents
    try:
        cursor.execute("ALTER TABLE ai_instances RENAME TO ai_agents")
        print("[SUCCESS] Renamed ai_instances to ai_agents")
    except Exception as e:
        print(f"[SKIP] ai_agents rename skipped: {e}")

    # 2. Add base_persona to ai_agents
    try:
        cursor.execute("ALTER TABLE ai_agents ADD COLUMN base_persona TEXT DEFAULT 'Helpful and friendly AI assistant.'")
        print("[SUCCESS] Added base_persona to ai_agents")
    except Exception as e:
        print(f"[SKIP] base_persona skip: {e}")

    # 3. Create chat_sessions table
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY,
                agent_id INTEGER,
                created_at FLOAT,
                messages JSON,
                FOREIGN KEY(agent_id) REFERENCES ai_agents(id)
            )
        """)
        print("[SUCCESS] Created chat_sessions table")
    except Exception as e:
        print(f"[ERROR] chat_sessions error: {e}")

    # 4. Migrate economy, house_state, journal_entries
    tables_to_migrate = ["economy", "house_state", "journal_entries"]
    for table in tables_to_migrate:
        cursor.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cursor.fetchall()]
        if "agent_id" not in cols and cols:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN agent_id INTEGER")
                print(f"[SUCCESS] Added agent_id to {table}")
                
                # Map data
                cursor.execute(f"""
                    UPDATE {table} 
                    SET agent_id = (SELECT id FROM ai_agents WHERE ai_agents.owner_id = {table}.owner_id)
                """)
                print(f"[SUCCESS] Mapped agent_id data for {table}")
                
                # Drop owner_id (SQLite 3.35.0+)
                try:
                    cursor.execute(f"ALTER TABLE {table} DROP COLUMN owner_id")
                    print(f"[SUCCESS] Dropped owner_id from {table}")
                except Exception as e:
                    print(f"[WARN] Could not drop owner_id from {table} (SQLite <3.35.0): {e}")
            except Exception as e:
                print(f"[ERROR] Error migrating table {table}: {e}")

    # Build mapping for ChromaDB
    try:
        cursor.execute("SELECT owner_id, id FROM ai_agents")
        mapping = {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        mapping = {}
        print(f"[SKIP] Mapping for ChromaDB skipped: {e}")
        
    conn.commit()
    conn.close()

    # 5. Migrate ChromaDB
    if os.path.exists(CHROMA_PATH) and mapping:
        try:
            client = chromadb.PersistentClient(path=CHROMA_PATH)
            collection = client.get_collection("ai_memory")
            data = collection.get()
            if data and "ids" in data and len(data["ids"]) > 0:
                updated_metadatas = []
                ids_to_update = []
                for i, metadata in enumerate(data["metadatas"]):
                    if metadata and "user_id" in metadata:
                        user_id = metadata["user_id"]
                        if user_id in mapping:
                            new_meta = metadata.copy()
                            new_meta["agent_id"] = mapping[user_id]
                            # del new_meta["user_id"]  # keep it for safety during transition
                            updated_metadatas.append(new_meta)
                            ids_to_update.append(data["ids"][i])
                            
                if ids_to_update:
                    collection.update(ids=ids_to_update, metadatas=updated_metadatas)
                    print(f"[SUCCESS] Migrated {len(ids_to_update)} ChromaDB memories to use agent_id.")
            else:
                print("[INFO] No ChromaDB memories to migrate.")
        except Exception as e:
            print(f"[WARN] ChromaDB migration skipped/error: {e}")
    else:
        print("[INFO] No ChromaDB found or no mappings.")

    print("Migration complete!")

if __name__ == "__main__":
    migrate()
