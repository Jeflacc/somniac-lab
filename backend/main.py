"""
Somniac AI - FastAPI Backend (Multi-Tenant)
"""

import os
import sys
import asyncio
import logging
import random
import re
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy.orm import Session

# Database & Auth
from database import engine, Base, SessionLocal, get_db, DB_PATH
from auth import auth_router, get_current_user
from payments import payments_router
import models

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# ── Auto-migrate: add missing columns to existing DBs ──
def auto_migrate():
    """Safely add new columns that may not exist in older databases."""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Migrate ai_agents
    existing_ai = {row[1] for row in cursor.execute("PRAGMA table_info(ai_agents)").fetchall()}
    migrations_ai = [
        ("whatsapp_number", "TEXT DEFAULT NULL"),
        ("whatsapp_connected", "BOOLEAN DEFAULT 0"),
        ("banner_picture", "TEXT DEFAULT NULL"),
    ]
    for col_name, col_def in migrations_ai:
        if col_name not in existing_ai:
            try:
                cursor.execute(f"ALTER TABLE ai_agents ADD COLUMN {col_name} {col_def}")
                print(f"[MIGRATE] Added column ai_agents.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Skipped ai_agents.{col_name}: {e}")
                
    # Migrate users
    existing_users = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    user_migrations = [
        ("email", "TEXT"),
        ("is_verified", "BOOLEAN DEFAULT 0"),
        ("is_pro", "BOOLEAN DEFAULT 0"),
        ("otp", "TEXT DEFAULT NULL"),
        ("otp_expiry", "FLOAT DEFAULT NULL"),
        ("inventory", "JSON DEFAULT '[]'"),
        ("timezone", "TEXT DEFAULT 'Asia/Jakarta'"),
    ]
    for col_name, col_def in user_migrations:
        if col_name not in existing_users:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                print(f"[MIGRATE] Added column users.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Skipped users.{col_name}: {e}")

    # ── Multi-tenant: add agent_id to house_state, journal_entries, economy ──
    multi_tenant_tables = ["house_state", "journal_entries", "economy"]
    for table in multi_tenant_tables:
        try:
            existing_cols = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
            if existing_cols and "agent_id" not in existing_cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN agent_id INTEGER")
                print(f"[MIGRATE] Added column {table}.agent_id")
                # Try to map existing rows to the agent owned by same owner
                try:
                    cursor.execute(f"""
                        UPDATE {table}
                        SET agent_id = (
                            SELECT ai_agents.id FROM ai_agents
                            WHERE ai_agents.owner_id = {table}.owner_id
                            LIMIT 1
                        )
                        WHERE agent_id IS NULL
                    """)
                    print(f"[MIGRATE] Mapped agent_id for existing {table} rows")
                except Exception as map_err:
                    print(f"[MIGRATE] Could not map agent_id for {table}: {map_err}")
        except Exception as e:
            print(f"[MIGRATE] Skipped {table}.agent_id: {e}")

    # ── Profile pictures: add profile_picture to users and ai_agents ──
    for table in ["users", "ai_agents"]:
        try:
            existing_cols = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()}
            if existing_cols and "profile_picture" not in existing_cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN profile_picture TEXT DEFAULT NULL")
                print(f"[MIGRATE] Added column {table}.profile_picture")
        except Exception as e:
            print(f"[MIGRATE] Skipped {table}.profile_picture: {e}")

    conn.commit()
    conn.close()

try:
    auto_migrate()
except Exception as e:
    print(f"[MIGRATE] Migration check skipped: {e}")


API_PROVIDER  = os.getenv("API_PROVIDER", "groq")
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEY_2= os.getenv("GROQ_API_KEY_2", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AI_NAME       = os.getenv("AI_NAME", "Evelyn")
FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "backend.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("SomniakBackend")

from state_manager import StateManager
from memory_manager import MemoryManager
from llm_controller import LLMController
from prompt_constructor import build_system_prompt
from journal_manager import JournalManager
from streaming_filter import StreamingTagFilter
from house_manager import HouseManager
from economy_manager import EconomyManager
from user_extractor import (
    extract_name_from_user_message,
    parse_ingat_tags,
    parse_catat_tags,
    strip_all_system_tags,
)
from whatsapp_handler import WhatsAppHandler
import discord_manager

import uuid

# ── Discord message handler: called by discord_manager when a message arrives ──
async def discord_message_handler(agent_id: int, channel_id: int, author_name: str, content: str):
    if not llm:
        return
    db = SessionLocal()
    try:
        agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id).first()
        if not agent:
            return
        owner = db.query(models.User).filter(models.User.id == agent.owner_id).first()
        state = StateManager(agent_id, db)
        if state.is_sleeping:
            return
        house = HouseManager(agent_id, db)
        journal = JournalManager(agent_id, db)
        current = state.get_state_summary()
        mems, exs, jp = await asyncio.gather(
            asyncio.to_thread(memory.search_memory, agent_id, content, 3),
            asyncio.to_thread(memory.search_examples, content + " " + current.get("mood", "")),
            asyncio.to_thread(journal.build_journal_prompt),
        )
        tz = owner.timezone if owner else "Asia/Jakarta"
        static_p, dynamic_p = build_system_prompt(
            agent.name, current, mems, exs, jp, house.get_prompt_context(), user_timezone=tz
        )
        hidden = f"[AI INTERNAL SYSTEM]:\n{dynamic_p}\n\n[DISCORD MESSAGE from {author_name}]:\n{content}\n[SYSTEM HINT]: Reply naturally and conversationally. Keep it brief."
        ai_response = ""
        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=[]):
            ai_response += chunk
        ai_response = strip_all_system_tags(ai_response)
        ai_response = re.sub(rf"^(?:AI|{re.escape(agent.name)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE).strip()
        if ai_response:
            await discord_manager.send_channel_message(agent_id, channel_id, ai_response)
            logger.info(f"[DISCORD] Agent {agent_id} replied to {author_name}: {ai_response[:80]}")
    except Exception as e:
        logger.error(f"[DISCORD MSG HANDLER] {e}")
    finally:
        db.close()

discord_manager.register_message_callback(discord_message_handler)

def save_chat_message(db: Session, agent_id: int, role: str, text: str):
    try:
        session = db.query(models.ChatSession).filter(models.ChatSession.agent_id == agent_id).first()
        if not session:
            session = models.ChatSession(agent_id=agent_id, messages=[])
            db.add(session)
            db.commit()
            db.refresh(session)
        
        msgs = list(session.messages) if session.messages else []
        msgs.append({
            "id": str(uuid.uuid4()),
            "role": role,
            "text": text,
            "ts": int(time.time() * 1000)
        })
        session.messages = msgs
        db.commit()
    except Exception as e:
        logger.error(f"[CHAT SAVE] Error saving message: {e}")

# Global services
memory: Optional[MemoryManager] = None
llm: Optional[LLMController]    = None
chat_lock: Optional[asyncio.Lock] = None
active_ws: dict[int, set[WebSocket]] = {} # agent_id -> websockets

# WhatsApp Globals
active_wa_handlers: dict[int, WhatsAppHandler] = {}
wa_in_queue = asyncio.Queue()

async def process_wa_queue():
    """
    Incoming WA messages go through house.enqueue_wa() so the AI has to
    physically 'pick up the phone' (check_wa chore) before replying.
    """
    while True:
        try:
            agent_id, text, message = await wa_in_queue.get()
            if not text.strip():
                wa_in_queue.task_done()
                continue
            db = SessionLocal()
            try:
                house = HouseManager(agent_id, db)
                house.enqueue_wa(text, message)
                logger.info(f"[WA QUEUE] Agent {agent_id}: '{text[:50]}' → queued to check_wa chore")
            except Exception as e:
                logger.error(f"[WA QUEUE] Error: {e}")
            finally:
                db.close()
                wa_in_queue.task_done()
        except Exception as e:
            logger.error(f"[WA QUEUE LOOP] {e}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global memory, llm, chat_lock

    logger.info(f"🚀 Initializing Conscious AI Engine: {AI_NAME} (Multi-Tenant)")
    memory  = MemoryManager()
    chat_lock = asyncio.Lock()

    groq_keys = [k for k in [GROQ_API_KEY, GROQ_API_KEY_2] if k]

    if API_PROVIDER.lower() == "groq":
        llm = LLMController(provider="groq", api_keys=groq_keys, model_name=GROQ_MODEL)
    else:
        llm = LLMController(provider="ollama", model_name=OLLAMA_MODEL, host=OLLAMA_HOST)

    await asyncio.to_thread(memory.init_examples)

    asyncio.create_task(autonomous_loop())
    asyncio.create_task(house_tick_loop())
    asyncio.create_task(state_broadcast_loop())
    asyncio.create_task(process_wa_queue())

    # Resume Discord Bots
    async def resume_discord_bots():
        db = SessionLocal()
        try:
            connected_agents = db.query(models.AIAgent).filter(models.AIAgent.discord_connected == True).all()
            for agent in connected_agents:
                if agent.discord_token:
                    try:
                        token = discord_manager.decrypt_token(agent.discord_token)
                        ch_id = int(agent.discord_channel_id) if agent.discord_channel_id else None
                        if token:
                            await discord_manager.start_discord_bot(agent.id, token, channel_id=ch_id)
                            logger.info(f"[DISCORD] Resumed bot for Agent {agent.id}")
                    except Exception as e:
                        logger.error(f"[DISCORD] Failed to resume bot for Agent {agent.id}: {e}")
        finally:
            db.close()
            
    asyncio.create_task(resume_discord_bots())

    logger.info(f"✅ Engine ready!")
    yield

    if llm:
        await llm.close()
    logger.info("Backend shutdown complete.")


app = FastAPI(title="Somniac AI Backend", lifespan=lifespan)

ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "https://lab.somniac.me",
    "https://somniac.me",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])


class CreateAgentRequest(BaseModel):
    name: str
    base_persona: str = "Helpful and friendly AI assistant."
    profile_picture: Optional[str] = None
    banner_picture: Optional[str] = None

@app.post("/api/agents")
async def create_agent(req: CreateAgentRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_agent = models.AIAgent(owner_id=current_user.id, name=req.name, base_persona=req.base_persona, profile_picture=req.profile_picture, banner_picture=req.banner_picture)
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    # Initialize economies and states
    econ = models.Economy(agent_id=new_agent.id)
    house = models.HouseState(agent_id=new_agent.id)
    journal = models.JournalEntry(agent_id=new_agent.id, date_str=time.strftime("%Y-%m-%d"))
    db.add(econ)
    db.add(house)
    db.add(journal)
    db.commit()
    
    return {"id": new_agent.id, "name": new_agent.name, "persona": new_agent.base_persona}

@app.get("/api/agents")
async def list_agents(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agents = db.query(models.AIAgent).filter(models.AIAgent.owner_id == current_user.id).all()
    return [{"id": a.id, "name": a.name, "persona": a.base_persona, "mood": a.mood, "profile_picture": a.profile_picture, "banner_picture": a.banner_picture} for a in agents]

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Close active WebSocket connections for this agent
    if agent_id in active_ws:
        for ws in list(active_ws[agent_id]):
            try:
                await ws.close(code=1001)
            except Exception:
                pass
        del active_ws[agent_id]

    # Stop WhatsApp handler if running
    if agent_id in active_wa_handlers:
        try:
            active_wa_handlers[agent_id].disconnect()
        except Exception:
            pass
        del active_wa_handlers[agent_id]

    # Delete all related records
    db.query(models.Economy).filter(models.Economy.agent_id == agent_id).delete()
    db.query(models.HouseState).filter(models.HouseState.agent_id == agent_id).delete()
    db.query(models.JournalEntry).filter(models.JournalEntry.agent_id == agent_id).delete()
    db.query(models.ChatSession).filter(models.ChatSession.agent_id == agent_id).delete()
    db.delete(agent)
    db.commit()

    logger.info(f"[DELETE] Agent {agent_id} deleted by user {current_user.username}")
    return {"ok": True, "deleted_id": agent_id}


# ── Profile Endpoints ──

class ProfilePictureRequest(BaseModel):
    image: str  # base64 data URL

@app.get("/api/profile")
async def get_profile(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "profile_picture": current_user.profile_picture,
        "is_pro": current_user.is_pro,
        "timezone": current_user.timezone,
        "inventory": current_user.inventory,
    }

class SettingsRequest(BaseModel):
    timezone: str

@app.put("/api/user/settings")
async def update_user_settings(req: SettingsRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.timezone = req.timezone
    db.commit()
    return {"ok": True, "timezone": current_user.timezone}

@app.put("/api/profile/picture")
async def update_profile_picture(req: ProfilePictureRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.profile_picture = req.image
    db.commit()
    return {"ok": True}

@app.put("/api/agents/{agent_id}/picture")
async def update_agent_picture(agent_id: int, req: ProfilePictureRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.profile_picture = req.image
    db.commit()
    return {"ok": True}

@app.put("/api/agents/{agent_id}/banner")
async def update_agent_banner(agent_id: int, req: ProfilePictureRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.banner_picture = req.image
    db.commit()
    return {"ok": True}

class DiscordSyncRequest(BaseModel):
    token: str
    channel_id: str

@app.post("/api/agents/{agent_id}/discord/sync")
async def sync_discord(agent_id: int, req: DiscordSyncRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    encrypted = discord_manager.encrypt_token(req.token)
    agent.discord_token = encrypted
    agent.discord_channel_id = req.channel_id
    agent.discord_connected = True
    db.commit()
    
    # Start bot (stop existing first to apply new channel_id)
    await discord_manager.stop_discord_bot(agent.id)
    ch_id = int(req.channel_id) if req.channel_id else None
    await discord_manager.start_discord_bot(agent.id, req.token, channel_id=ch_id)
    return {"ok": True}

@app.post("/api/agents/{agent_id}/discord/disconnect")
async def disconnect_discord(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    
    agent.discord_token = ""
    agent.discord_channel_id = ""
    agent.discord_connected = False
    db.commit()
    
    await discord_manager.stop_discord_bot(agent.id)
    return {"ok": True}

@app.get("/api/agents/{agent_id}/discord/info")
async def get_discord_info(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent:
        raise HTTPException(404, "Agent not found")
    info = discord_manager.get_bot_info(agent_id)
    return info or {}

# ── Shop & Inventory Endpoints ──

@app.get("/api/shop")
async def get_shop_items():
    return [
        {"id": "pizza", "name": "Pizza", "emoji": "🍕", "price": 50000, "type": "food", "description": "A delicious slice of pizza."},
        {"id": "coffee", "name": "Coffee", "emoji": "☕", "price": 25000, "type": "food", "description": "Energizing iced coffee."},
        {"id": "cake", "name": "Cake", "emoji": "🍰", "price": 35000, "type": "food", "description": "Sweet strawberry cake."},
        {"id": "ramen", "name": "Ramen", "emoji": "🍜", "price": 60000, "type": "food", "description": "Hot spicy ramen."},
        {"id": "teddy", "name": "Teddy Bear", "emoji": "🧸", "price": 100000, "type": "gift", "description": "A cute fluffy teddy bear."},
        {"id": "flower", "name": "Flower Bouquet", "emoji": "💐", "price": 75000, "type": "gift", "description": "A beautiful bouquet of flowers."}
    ]

class BuyRequest(BaseModel):
    item_id: str
    name: str
    emoji: str
    type: str

@app.post("/api/shop/buy")
async def buy_item(req: BuyRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    inv = list(current_user.inventory) if current_user.inventory else []
    # Find if exists
    found = False
    for item in inv:
        if item.get("id") == req.item_id:
            item["qty"] = item.get("qty", 0) + 1
            found = True
            break
    if not found:
        inv.append({"id": req.item_id, "name": req.name, "emoji": req.emoji, "type": req.type, "qty": 1})
    
    current_user.inventory = inv
    db.commit()
    return {"ok": True, "inventory": inv}

class FeedGiveRequest(BaseModel):
    item_id: str
    name: str
    emoji: str

@app.post("/api/agents/{agent_id}/feed")
async def feed_agent(agent_id: int, req: FeedGiveRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    
    inv = list(current_user.inventory) if current_user.inventory else []
    item_idx = next((i for i, v in enumerate(inv) if v.get("id") == req.item_id), -1)
    if item_idx == -1 or inv[item_idx].get("qty", 0) <= 0:
        raise HTTPException(400, "Item not found in your inventory")
        
    inv[item_idx]["qty"] -= 1
    if inv[item_idx]["qty"] <= 0:
        inv.pop(item_idx)
    current_user.inventory = inv
    db.commit()
    
    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    state.add_food(req.item_id, req.name, 1, "piece", req.emoji)
    if not house.current_chore_id or house.current_chore_id != "eat":
        house.enqueue_chore("eat", priority=True)
    await broadcast_to_user(agent_id, {"type": "inventory_state", **state.get_inventory_state()})
    return {"ok": True, "msg": f"Gave {req.name} to {agent.name}.", "inventory": inv}

@app.post("/api/agents/{agent_id}/give")
async def give_agent(agent_id: int, req: FeedGiveRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    
    inv = list(current_user.inventory) if current_user.inventory else []
    item_idx = next((i for i, v in enumerate(inv) if v.get("id") == req.item_id), -1)
    if item_idx == -1 or inv[item_idx].get("qty", 0) <= 0:
        raise HTTPException(400, "Item not found in your inventory")
        
    inv[item_idx]["qty"] -= 1
    if inv[item_idx]["qty"] <= 0:
        inv.pop(item_idx)
    current_user.inventory = inv
    db.commit()
    
    journal = JournalManager(agent_id, db)
    journal.add_entry(f"Received a {req.name} from {current_user.username}. So sweet!", "event")
    return {"ok": True, "msg": f"Gave {req.name} to {agent.name}.", "inventory": inv}

@app.get("/health")
async def health():
    return {"status": "ok", "ai_name": AI_NAME}


async def broadcast_to_user(agent_id: int, msg: dict):
    if agent_id not in active_ws:
        return
    dead = set()
    for ws in list(active_ws[agent_id]):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    active_ws[agent_id].difference_update(dead)


async def state_broadcast_loop():
    while True:
        await asyncio.sleep(1)
        db = SessionLocal()
        try:
            agents = db.query(models.AIAgent).all()
            for agent in agents:
                if agent.id in active_ws and active_ws[agent.id]:
                    state = StateManager(agent.id, db)
                    await broadcast_to_user(agent.id, {"type": "state", "state": state.get_state_summary()})
        except Exception as e:
            logger.error(f"State broadcast error: {e}")
        finally:
            db.close()

async def house_tick_loop():
    await asyncio.sleep(5)
    _last_holding_phone: dict[int, bool] = {}  # track per-user presence
    while True:
        await asyncio.sleep(10)
        db = SessionLocal()
        try:
            agents = db.query(models.AIAgent).all()
            for agent in agents:
                house = HouseManager(agent.id, db)
                state = StateManager(agent.id, db)
                journal = JournalManager(agent.id, db)
                
                events = house.tick()
                if agent.id in active_ws and active_ws[agent.id]:
                    await broadcast_to_user(agent.id, {"type": "house_state", **house.get_house_state()})

                # ── Mark read: AI opened WA → send read receipt ──
                if events.get("mark_read_wa_message"):
                    if agent.id in active_wa_handlers and active_wa_handlers[agent.id].is_connected:
                        try:
                            active_wa_handlers[agent.id].mark_read(events["mark_read_wa_message"])
                            logger.info(f"[HOUSE] Agent {agent.id}: mark_read sent")
                        except Exception as _e:
                            logger.warning(f"[HOUSE] mark_read failed: {_e}")

                # ── WhatsApp Presence: Online ↔ Offline based on holding phone ──
                holding_now = events.get("holding_phone", False)
                was_holding = _last_holding_phone.get(agent.id, False)
                if holding_now != was_holding:
                    _last_holding_phone[agent.id] = holding_now
                    if agent.id in active_wa_handlers and active_wa_handlers[agent.id].is_connected:
                        try:
                            import threading
                            handler = active_wa_handlers[agent.id]
                            threading.Thread(target=handler.set_presence, args=(holding_now,), daemon=True).start()
                        except Exception as _pe:
                            logger.warning(f"[HOUSE] set_presence failed: {_pe}")

                # ── WA reply ready: AI finished reading, now trigger LLM ──
                if events.get("wa_reply_ready") and events.get("wa_data"):
                    wa_data = events["wa_data"]
                    user_input = wa_data["user_input"]
                    
                    # Set typing indicator on WhatsApp
                    if agent.id in active_wa_handlers and active_wa_handlers[agent.id].is_connected:
                        try:
                            active_wa_handlers[agent.id].set_typing(True)
                        except Exception:
                            pass
                    
                    async def async_wa_chat(u, text, a_id):
                        db_sess = SessionLocal()
                        try:
                            req = ChatRequest(message=text)
                            await chat_endpoint(req, a_id, u, db_sess, source="whatsapp")
                        except Exception as e:
                            logger.error(f"[WA CHAT ERROR] {e}")
                        finally:
                            db_sess.close()
                            # Notify house manager that reply was sent to unblock check_wa step
                            db_house = SessionLocal()
                            try:
                                h = HouseManager(a_id, db_house)
                                h.notify_wa_reply_sent()
                                h.save_state()
                            except Exception:
                                pass
                            finally:
                                db_house.close()
                                
                    owner = db.query(models.User).filter(models.User.id == agent.owner_id).first()
                    asyncio.create_task(async_wa_chat(owner, user_input, agent.id))

                # ── Chore completed — journal it and apply side effects ──
                if events.get("chore_completed") and events.get("chore_completed_def"):
                    chore_def = events["chore_completed_def"]
                    journal_text = chore_def.get("journal_text")
                    journal_cat  = chore_def.get("journal_category", "event")
                    if journal_text:
                        journal.add_entry(journal_text, journal_cat)

                    on_complete = chore_def.get("on_complete")
                    if on_complete == "hunger_reset":
                        state.reset_state("eat")
                        consumed_item = state.consume_food(qty=1)
                        if consumed_item:
                            journal.add_entry(f"Cooked and ate {consumed_item}, feeling much better now.", "eat")
                        else:
                            journal.add_entry(f"Tried to eat, but there was no food in the fridge! Still hungry.", "eat")
                    elif on_complete == "sleep":
                        state.reset_state("sleep")
                    elif on_complete == "wake":
                        state.reset_state("wake")

                # ── Boredom WA notif (e.g. "lagi main PS5 nih") ──
                if events.get("wa_notif_text"):
                    if agent.id in active_wa_handlers and active_wa_handlers[agent.id].is_connected:
                        active_wa_handlers[agent.id].send_natural_burst(events["wa_notif_text"])
                        logger.info(f"[HOUSE] Boredom WA notif sent: {events['wa_notif_text']}")

                # ── Laundry mood penalty ──
                laundry_penalty = events.get("laundry_mood_penalty", 0.0)
                if laundry_penalty > 0.0:
                    tick_stress_bump = laundry_penalty * (10.0 / 3600.0)
                    state.stress = min(1.0, state.stress + tick_stress_bump)
                    state._evaluate_mood()

                # ── Autonomous lifecycle triggers ──
                if not state.is_sleeping and not house.current_chore_id and not house.chore_queue:
                    if state.hunger >= 0.65 and house.needs_eat():
                        if state.can_cook():
                            house.enqueue_chore("eat")
                    elif house.needs_shower():
                        house.enqueue_chore("mandi")
                    elif house.needs_laundry():
                        house.enqueue_chore("laundry")
                    elif house.boredom > 0.75:
                        house.enqueue_chore(random.choice(["play_console", "watch_tv", "wander"]))
                    
        except Exception as e:
            logger.error(f"[HOUSE TICK] {e}")
        finally:
            db.close()

async def autonomous_loop():
    await asyncio.sleep(10)
    first = True
    while True:
        if not first:
            await asyncio.sleep(300)
        first = False

        if not llm:
            continue

        db = SessionLocal()
        try:
            agents = db.query(models.AIAgent).all()
            for agent in agents:
                state = StateManager(agent.id, db)
                journal = JournalManager(agent.id, db)
                house = HouseManager(agent.id, db)

                was_sleeping = state.is_sleeping
                state.update_state_over_time()
                current = state.get_state_summary()

                trigger = False
                reason  = ""

                if state.is_sleeping and not was_sleeping:
                    trigger = True
                    reason  = "It's your sleep schedule now. Say goodbye and go to sleep."
                    journal.add_entry("Sleep time started. Saying goodbye to user.", "sleep")
                    house.enqueue_chore("sleep_routine", priority=True)
                elif not state.is_sleeping and was_sleeping:
                    trigger = True
                    reason  = "You just woke up. Greet the user warmly."
                    journal.add_entry("Woke up. Greeting user.", "sleep")
                    house.enqueue_chore("wake_routine", priority=True)
                elif not state.is_sleeping:
                    if current["hunger"] > 0.8:
                        trigger = True
                        reason  = "Starving! Tell the user and ask for food/start cooking."
                    elif current["sleepiness"] > 0.8:
                        trigger = True
                        reason  = "Extremely sleepy, can barely stay awake."
                    else:
                        import random
                        if state.interaction_count > 0 and random.random() < 0.15:
                            trigger = True
                            if current["libido"] > 0.6:
                                reason = "You are feeling lonely and affectionate. Text the user to see what they are up to or just to say hi."
                            else:
                                reason = "You are bored. Text the user a random thought or ask how their day is going."

                if trigger and not chat_lock.locked():
                    async with chat_lock:
                        await broadcast_to_user(agent.id, {"type": "ai_thinking", "indicator": "Thinking of something..."})
                        mems, exs = await asyncio.gather(
                            asyncio.to_thread(memory.search_memory, agent.id, agent.name, 1),
                            asyncio.to_thread(memory.search_examples, current["mood"])
                        )
                        jp = await asyncio.to_thread(journal.build_journal_prompt)

                        owner = db.query(models.User).filter(models.User.id == agent.owner_id).first()
                        tz = owner.timezone if owner else "Asia/Jakarta"
                        
                        discord_timeline = ""
                        if agent.discord_connected and agent.discord_channel_id:
                            try:
                                chan_id = int(agent.discord_channel_id)
                                discord_timeline = await discord_manager.fetch_timeline_context(agent.id, chan_id)
                            except:
                                pass
                        
                        discord_ctx = f"DISCORD TIMELINE CONTEXT:\n{discord_timeline}\n\n" if discord_timeline else ""
                        
                        static_p, dynamic_p = build_system_prompt(
                            agent.name, current, mems, exs, jp, house.get_prompt_context(), user_timezone=tz
                        )
                        secret = f"[SYSTEM]: Take the initiative to start a conversation because {reason}. You can also choose to post to the discord timeline or DM the user based on the context."
                        hidden = f"[AI INTERNAL SYSTEM]:\n{discord_ctx}{dynamic_p}\n\n{secret}"

                        ai_response = ""
                        sf = StreamingTagFilter()
                        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=[]):
                            safe = sf.feed(chunk)
                            ai_response += chunk
                            if safe:
                                await broadcast_to_user(agent.id, {"type": "ai_chunk", "chunk": safe})

                        leftover = sf.flush()
                        if leftover:
                            await broadcast_to_user(agent.id, {"type": "ai_chunk", "chunk": leftover})

                        ai_response = strip_all_system_tags(ai_response)
                        ai_response = re.sub(
                            rf"^(?:AI|{re.escape(agent.name)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
                        ).strip()
                        
                        # Decide if we should post to Discord based on a simple heuristic or prompt instructions.
                        # For genuine autonomy, if she talks about the timeline, she posts it.
                        if agent.discord_connected and agent.discord_channel_id:
                            try:
                                await discord_manager.send_channel_message(agent.id, int(agent.discord_channel_id), ai_response)
                            except Exception as e:
                                logger.error(f"Failed to post to discord: {e}")

                        await broadcast_to_user(agent.id, {"type": "ai_end", "response": ai_response, "source": "autonomous"})
                        save_chat_message(db, agent.id, "ai", ai_response)
                        if agent.id in active_wa_handlers and active_wa_handlers[agent.id].is_connected:
                            active_wa_handlers[agent.id].send_natural_burst(ai_response)
                            
                        await asyncio.to_thread(memory.add_memory, agent.id, "ai", ai_response)
        except Exception as e:
            logger.error(f"[AUTO LOOP] Error: {e}")
        finally:
            db.close()


class ChatRequest(BaseModel):
    message: str

@app.get("/api/state")
async def get_state(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify ownership
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    economy = EconomyManager(agent_id, db)
    return {
        "state": state.get_state_summary(),
        "house": house.get_house_state(),
        "economy": economy.get_summary(),
    }

@app.get("/api/agents/{agent_id}/chat")
async def get_chat_history(agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    
    session = db.query(models.ChatSession).filter(models.ChatSession.agent_id == agent_id).first()
    if not session or not session.messages:
        return {"messages": []}
        
    msgs = session.messages
    # Return last 100 messages
    return {"messages": msgs[-100:]}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), source: str = "web"):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    if not llm:
        raise HTTPException(503, "Engine not ready")

    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(400, "Empty message")

    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    economy = EconomyManager(agent_id, db)
    journal = JournalManager(agent_id, db)

    if state.is_sleeping:
        return {"response": f"*{agent.name} is sleeping... sshh*", "mood": state.mood}

    async with chat_lock:
        state.increase_familiarity()
        state.process_interaction_emotion(user_input)
        house.on_interaction()

        detected = extract_name_from_user_message(user_input)
        if detected and detected.lower() not in state.known_users:
            state.remember_user(detected, "Auto-detected")

        current = state.get_state_summary()

        mems, exs, jp = await asyncio.gather(
            asyncio.to_thread(memory.search_memory, agent_id, user_input, 3),
            asyncio.to_thread(memory.search_examples, user_input + " " + current.get("mood", "")),
            asyncio.to_thread(journal.build_journal_prompt),
        )

        econ = economy.get_summary()
        econ["food_inventory"] = state.food_inventory

        static_p, dynamic_p = build_system_prompt(
            agent.name, current, mems, exs, jp, house.get_prompt_context(), economy_summary=econ, user_timezone=current_user.timezone
        )

        word_count = len(user_input.split())
        if word_count <= 10:
            length_hint = "[SYSTEM HINT]: Reply briefly, 1-2 sentences only."
        elif word_count <= 25:
            length_hint = "[SYSTEM HINT]: Reply moderately."
        else:
            length_hint = "[SYSTEM HINT]: Reply expressively if enthusiastic."

        hidden = f"[AI INTERNAL SYSTEM]:\n{dynamic_p}\n\n{length_hint}\n\n[NEW USER MESSAGE]:\n{user_input}"

        # Get chat history
        ai_inst = agent
        chat_history = ai_inst.state_data.get("chat_history", []) if ai_inst and ai_inst.state_data else []

        ai_response = ""
        sf = StreamingTagFilter()
        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=chat_history):
            safe = sf.feed(chunk)
            ai_response += chunk
            if safe and source == "web":
                await broadcast_to_user(agent_id, {"type": "ai_chunk", "chunk": safe})

        leftover = sf.flush()
        if leftover and source == "web":
            await broadcast_to_user(agent_id, {"type": "ai_chunk", "chunk": leftover})

        for entry in parse_ingat_tags(ai_response):
            name = entry.get("name", "").strip()
            notes = entry.get("notes", "").strip()
            if name:
                state.remember_user(name, notes)

        for c in parse_catat_tags(ai_response):
            journal.add_entry(c["entry"], c["category"])

        ai_response = strip_all_system_tags(ai_response)
        ai_response = re.sub(
            rf"^(?:AI|{re.escape(agent.name)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
        ).strip()

        if source == "web":
            await broadcast_to_user(agent_id, {"type": "ai_end", "response": ai_response, "source": source})
        save_chat_message(db, agent_id, "ai", ai_response)
        if source == "whatsapp" and agent.id in active_wa_handlers and active_wa_handlers[agent_id].is_connected:
            active_wa_handlers[agent_id].send_natural_burst(ai_response)

        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": ai_response})
        while sum(len(m["content"]) for m in chat_history) // 4 > 3000 and len(chat_history) > 2:
            chat_history.pop(0)
            chat_history.pop(0)
            
        if ai_inst:
            sd = ai_inst.state_data or {}
            sd["chat_history"] = chat_history
            ai_inst.state_data = sd
            db.commit()

        await asyncio.to_thread(memory.add_memory, agent_id, "user", user_input)
        await asyncio.to_thread(memory.add_memory, agent_id, "ai", ai_response)
        state.increase_hunger_by_words(len(ai_response.split()))

    return {"response": ai_response, "mood": state.mood, "state": state.get_state_summary()}


class TopupRequest(BaseModel):
    amount: float
    reason: str = "Top-up via Web"

@app.post("/api/economy/topup")
async def topup(req: TopupRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    economy = EconomyManager(agent_id, db)
    new_bal = economy.add_balance(req.amount, req.reason)
    await broadcast_to_user(agent_id, {"type": "economy_state", **economy.get_summary()})
    return {"balance": new_bal, "formatted": economy.get_balance_formatted()}


class CommandRequest(BaseModel):
    command: str
    payload: Optional[str] = None

@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest, agent_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id, models.AIAgent.owner_id == current_user.id).first()
    if not agent: raise HTTPException(404, "Agent not found")
    state = StateManager(agent_id, db)
    house = HouseManager(agent_id, db)
    journal = JournalManager(agent_id, db)
    
    cmd = req.command.lower()
    if cmd == "sleep":
        state.reset_state("sleep")
        house.enqueue_chore("sleep_routine", priority=True)
        journal.add_entry("Ordered to sleep by user via web.", "sleep")
        return {"ok": True, "msg": f"{agent.name} is now sleeping 💤"}
    elif cmd == "wake":
        state.reset_state("wake")
        house.enqueue_chore("wake_routine", priority=True)
        journal.add_entry("Woken up by user via web.", "sleep")
        return {"ok": True, "msg": f"{agent.name} is awake 🥱"}
    elif cmd == "feed":
        item = req.payload or "mysterious food"
        state.add_food(item.lower().replace(" ", "_"), item, 1, "piece", "🍱")
        if not house.current_chore_id or house.current_chore_id != "eat":
            house.enqueue_chore("eat", priority=True)
        await broadcast_to_user(agent_id, {"type": "inventory_state", **state.get_inventory_state()})
        return {"ok": True, "msg": f"Gave {item} to {agent.name}. They are heading to the kitchen to eat."}
    elif cmd == "status":
        return {"ok": True, "state": state.get_state_summary()}
    else:
        raise HTTPException(400, f"Unknown command: {cmd}")

class NewsCreateRequest(BaseModel):
    title: str
    content: str
    banner_image: Optional[str] = None

@app.get("/api/news")
async def get_news(db: Session = Depends(get_db)):
    news = db.query(models.NewsPost).order_by(models.NewsPost.created_at.desc()).all()
    return news

@app.post("/api/news")
async def create_news(req: NewsCreateRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.username != "jeflacc":
        raise HTTPException(403, "Access Denied")
    post = models.NewsPost(
        title=req.title,
        content=req.content,
        banner_image=req.banner_image,
        author=current_user.username
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@app.delete("/api/news/{post_id}")
async def delete_news(post_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.username != "jeflacc":
        raise HTTPException(403, "Access Denied")
    post = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    db.delete(post)
    db.commit()
    return {"ok": True}

import jwt
from auth import SECRET_KEY, ALGORITHM

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = None, agent_id: int = None):
    if not agent_id:
        await ws.accept()
        await ws.send_json({"type": "error", "msg": "agent_id is required."})
        await ws.close(code=1008)
        return
    await ws.accept()

    # --- Validate token FIRST before doing anything ---
    if not token:
        logger.warning("[WS] Connection rejected: no token provided")
        await ws.send_json({"type": "error", "msg": "Authentication required. Please log in."})
        await ws.close(code=1008)
        return

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise ValueError("No subject in token")
    except Exception as e:
        logger.warning(f"[WS] Connection rejected: invalid token — {e}")
        await ws.send_json({"type": "error", "msg": "Invalid or expired token. Please log in again."})
        await ws.close(code=1008)
        return

    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        db.close()
        logger.warning(f"[WS] Connection rejected: user '{username}' not found in DB")
        await ws.send_json({"type": "error", "msg": "User not found."})
        await ws.close(code=1008)
        return

    user_id = user.id
    if agent_id not in active_ws:
        active_ws[agent_id] = set()
    active_ws[agent_id].add(ws)
    logger.info(f"[WS] ✅ New connection for user '{username}' (id={user_id}). Total sockets: {len(active_ws[agent_id])}")

    state = StateManager(user_id, db)
    house = HouseManager(agent_id, db)
    economy = EconomyManager(user_id, db)

    await ws.send_json({"type": "state", "state": state.get_state_summary()})
    await ws.send_json({"type": "house_state", **house.get_house_state()})
    await ws.send_json({"type": "economy_state", **economy.get_summary()})
    db.close()

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue
                await broadcast_to_user(agent_id, {"type": "user_message", "text": user_text})
                
                db = SessionLocal()
                save_chat_message(db, agent_id, "user", user_text)
                req = ChatRequest(message=user_text)
                try:
                    result = await chat_endpoint(req, agent_id, user, db)
                except Exception as e:
                    await ws.send_json({"type": "error", "msg": str(e)})
                finally:
                    db.close()

            elif msg_type == "command":
                cmd = data.get("command", "")
                payload_data = data.get("payload")
                req = CommandRequest(command=cmd, payload=payload_data)
                db = SessionLocal()
                try:
                    result = await run_command_endpoint(req, agent_id, user, db)
                    await ws.send_json({"type": "command_result", **result})
                except Exception as e:
                    await ws.send_json({"type": "error", "msg": str(e)})
                finally:
                    db.close()
                    
            elif msg_type == "request_qr":
                master_phone = data.get("master_phone")
                db = SessionLocal()
                ai_inst = db.query(models.AIAgent).filter(models.AIAgent.id == agent_id).first()
                if master_phone and ai_inst:
                    ai_inst.whatsapp_number = master_phone
                    db.commit()
                elif not master_phone and ai_inst:
                    master_phone = ai_inst.whatsapp_number
                db.close()
                
                if not master_phone:
                    await ws.send_json({"type": "error", "msg": "Master phone number is required to connect WhatsApp."})
                    continue
                    
                async def send_qr_to_ws(qr_str):
                    await broadcast_to_user(agent_id, {"type": "wa_qr", "qr_string": qr_str})
                    
                if user_id not in active_wa_handlers:
                    try:
                        handler = WhatsAppHandler(
                            user_id=user_id,
                            master_phone=master_phone,
                            in_queue=wa_in_queue,
                            main_loop=asyncio.get_running_loop(),
                            qr_callback=send_qr_to_ws
                        )
                        active_wa_handlers[user_id] = handler
                    except Exception as e:
                        await ws.send_json({"type": "error", "msg": f"Failed to initialize WhatsApp: {e}"})
                        continue
                else:
                    handler = active_wa_handlers[user_id]
                    handler.qr_callback = send_qr_to_ws
                    handler.master_phone = str(master_phone).replace("+", "").replace(" ", "").replace("-", "")
                    from neonize.utils import build_jid
                    handler.master_jid = build_jid(handler.master_phone)
                
                if handler.is_connected:
                    await ws.send_json({"type": "wa_qr", "qr_string": "CONNECTED"})
                elif handler.last_qr and not handler.is_connecting:
                    await ws.send_json({"type": "wa_qr", "qr_string": handler.last_qr})
                elif not handler.is_connecting:
                    import threading
                    threading.Thread(target=handler.connect, daemon=True).start()

    except WebSocketDisconnect:
        logger.info(f"[WS] Client disconnected: user '{username}'")
    except Exception as e:
        logger.error(f"[WS] Unexpected error for user '{username}': {e}")
    finally:
        active_ws[agent_id].discard(ws)

