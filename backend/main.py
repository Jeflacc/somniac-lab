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
    
    # Migrate ai_instances
    existing_ai = {row[1] for row in cursor.execute("PRAGMA table_info(ai_instances)").fetchall()}
    migrations_ai = [
        ("whatsapp_number", "TEXT DEFAULT NULL"),
        ("whatsapp_connected", "BOOLEAN DEFAULT 0"),
    ]
    for col_name, col_def in migrations_ai:
        if col_name not in existing_ai:
            try:
                cursor.execute(f"ALTER TABLE ai_instances ADD COLUMN {col_name} {col_def}")
                print(f"[MIGRATE] Added column ai_instances.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Skipped ai_instances.{col_name}: {e}")
                
    # Migrate users
    existing_users = {row[1] for row in cursor.execute("PRAGMA table_info(users)").fetchall()}
    user_migrations = [
        ("email", "TEXT"),
        ("is_verified", "BOOLEAN DEFAULT 0"),
        ("is_pro", "BOOLEAN DEFAULT 0"),
        ("otp", "TEXT DEFAULT NULL"),
        ("otp_expiry", "FLOAT DEFAULT NULL"),
    ]
    for col_name, col_def in user_migrations:
        if col_name not in existing_users:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                print(f"[MIGRATE] Added column users.{col_name}")
            except Exception as e:
                print(f"[MIGRATE] Skipped users.{col_name}: {e}")
            
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

# Global services
memory: Optional[MemoryManager] = None
llm: Optional[LLMController]    = None
chat_lock: Optional[asyncio.Lock] = None
active_ws: dict[int, set[WebSocket]] = {} # user_id -> websockets

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
            user_id, text, message = await wa_in_queue.get()
            if not text.strip():
                wa_in_queue.task_done()
                continue
            db = SessionLocal()
            try:
                house = HouseManager(user_id, db)
                house.enqueue_wa(text, message)
                logger.info(f"[WA QUEUE] User {user_id}: '{text[:50]}' → queued to check_wa chore")
                await broadcast_to_user(user_id, {"type": "system", "text": f"[WhatsApp Incoming]: {text[:80]}"})
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

@app.get("/health")
async def health():
    return {"status": "ok", "ai_name": AI_NAME}


async def broadcast_to_user(user_id: int, msg: dict):
    if user_id not in active_ws:
        return
    dead = set()
    for ws in list(active_ws[user_id]):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    active_ws[user_id].difference_update(dead)


async def state_broadcast_loop():
    while True:
        await asyncio.sleep(1)
        db = SessionLocal()
        try:
            users = db.query(models.User).all()
            for user in users:
                if user.id in active_ws and active_ws[user.id]:
                    state = StateManager(user.id, db)
                    await broadcast_to_user(user.id, {"type": "state", "state": state.get_state_summary()})
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
            users = db.query(models.User).all()
            for user in users:
                house = HouseManager(user.id, db)
                state = StateManager(user.id, db)
                journal = JournalManager(user.id, db)
                
                events = house.tick()
                if user.id in active_ws and active_ws[user.id]:
                    await broadcast_to_user(user.id, {"type": "house_state", **house.get_house_state()})

                # ── Mark read: AI opened WA → send read receipt ──
                if events.get("mark_read_wa_message"):
                    if user.id in active_wa_handlers and active_wa_handlers[user.id].is_connected:
                        try:
                            active_wa_handlers[user.id].mark_read(events["mark_read_wa_message"])
                            logger.info(f"[HOUSE] User {user.id}: mark_read sent")
                        except Exception as _e:
                            logger.warning(f"[HOUSE] mark_read failed: {_e}")

                # ── WhatsApp Presence: Online ↔ Offline based on holding phone ──
                holding_now = events.get("holding_phone", False)
                was_holding = _last_holding_phone.get(user.id, False)
                if holding_now != was_holding:
                    _last_holding_phone[user.id] = holding_now
                    if user.id in active_wa_handlers and active_wa_handlers[user.id].is_connected:
                        try:
                            import threading
                            handler = active_wa_handlers[user.id]
                            threading.Thread(target=handler.set_presence, args=(holding_now,), daemon=True).start()
                        except Exception as _pe:
                            logger.warning(f"[HOUSE] set_presence failed: {_pe}")

                # ── WA reply ready: AI finished reading, now trigger LLM ──
                if events.get("wa_reply_ready") and events.get("wa_data"):
                    wa_data = events["wa_data"]
                    user_input = wa_data["user_input"]
                    
                    # Set typing indicator on WhatsApp
                    if user.id in active_wa_handlers and active_wa_handlers[user.id].is_connected:
                        try:
                            active_wa_handlers[user.id].set_typing(True)
                        except Exception:
                            pass
                    
                    async def async_wa_chat(u, text, uid):
                        db_sess = SessionLocal()
                        try:
                            req = ChatRequest(message=text)
                            await chat_endpoint(req, u, db_sess, source="whatsapp")
                        except Exception as e:
                            logger.error(f"[WA CHAT ERROR] {e}")
                        finally:
                            db_sess.close()
                            # Notify house manager that reply was sent to unblock check_wa step
                            db_house = SessionLocal()
                            try:
                                h = HouseManager(uid, db_house)
                                h.notify_wa_reply_sent()
                                h.save_state()
                            except Exception:
                                pass
                            finally:
                                db_house.close()
                                
                    asyncio.create_task(async_wa_chat(user, user_input, user.id))

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
                    elif on_complete == "sleep":
                        state.reset_state("sleep")
                    elif on_complete == "wake":
                        state.reset_state("wake")

                # ── Boredom WA notif (e.g. "lagi main PS5 nih") ──
                if events.get("wa_notif_text"):
                    if user.id in active_wa_handlers and active_wa_handlers[user.id].is_connected:
                        active_wa_handlers[user.id].send_natural_burst(events["wa_notif_text"])
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
                        house.enqueue_chore("eat")
                    elif house.needs_shower():
                        house.enqueue_chore("shower")
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
            users = db.query(models.User).all()
            for user in users:
                state = StateManager(user.id, db)
                journal = JournalManager(user.id, db)
                house = HouseManager(user.id, db)

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

                if trigger and not chat_lock.locked():
                    async with chat_lock:
                        await broadcast_to_user(user.id, {"type": "ai_thinking", "indicator": "Thinking of something..."})
                        mems, exs = await asyncio.gather(
                            asyncio.to_thread(memory.search_memory, user.id, AI_NAME, 1),
                            asyncio.to_thread(memory.search_examples, current["mood"])
                        )
                        jp = await asyncio.to_thread(journal.build_journal_prompt)

                        static_p, dynamic_p = build_system_prompt(
                            AI_NAME, current, mems, exs, jp, house.get_prompt_context()
                        )
                        secret = f"[SYSTEM]: Take the initiative to start a conversation because {reason}"
                        hidden = f"[AI INTERNAL SYSTEM]:\n{dynamic_p}\n\n{secret}"

                        ai_response = ""
                        sf = StreamingTagFilter()
                        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=[]):
                            safe = sf.feed(chunk)
                            ai_response += chunk
                            if safe:
                                await broadcast_to_user(user.id, {"type": "ai_chunk", "chunk": safe})

                        leftover = sf.flush()
                        if leftover:
                            await broadcast_to_user(user.id, {"type": "ai_chunk", "chunk": leftover})

                        ai_response = strip_all_system_tags(ai_response)
                        ai_response = re.sub(
                            rf"^(?:AI|{re.escape(AI_NAME)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
                        ).strip()
                        await broadcast_to_user(user.id, {"type": "ai_end", "response": ai_response, "source": "autonomous"})
                        if user.id in active_wa_handlers and active_wa_handlers[user.id].is_connected:
                            active_wa_handlers[user.id].send_natural_burst(ai_response)
                            
                        await asyncio.to_thread(memory.add_memory, user.id, "ai", ai_response)
        except Exception as e:
            logger.error(f"[AUTO LOOP] Error: {e}")
        finally:
            db.close()


class ChatRequest(BaseModel):
    message: str

@app.get("/api/state")
async def get_state(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = StateManager(current_user.id, db)
    house = HouseManager(current_user.id, db)
    economy = EconomyManager(current_user.id, db)
    return {
        "state": state.get_state_summary(),
        "house": house.get_house_state(),
        "economy": economy.get_summary(),
    }

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db), source: str = "web"):
    if not llm:
        raise HTTPException(503, "Engine not ready")

    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(400, "Empty message")

    state = StateManager(current_user.id, db)
    house = HouseManager(current_user.id, db)
    economy = EconomyManager(current_user.id, db)
    journal = JournalManager(current_user.id, db)

    if state.is_sleeping:
        return {"response": f"*{AI_NAME} is sleeping... sshh*", "mood": state.mood}

    async with chat_lock:
        state.increase_familiarity()
        state.process_interaction_emotion(user_input)
        house.on_interaction()

        detected = extract_name_from_user_message(user_input)
        if detected and detected.lower() not in state.known_users:
            state.remember_user(detected, "Auto-detected")

        current = state.get_state_summary()

        mems, exs, jp = await asyncio.gather(
            asyncio.to_thread(memory.search_memory, current_user.id, user_input, 3),
            asyncio.to_thread(memory.search_examples, user_input + " " + current.get("mood", "")),
            asyncio.to_thread(journal.build_journal_prompt),
        )

        econ = economy.get_summary()
        econ["food_inventory"] = state.food_inventory

        static_p, dynamic_p = build_system_prompt(
            AI_NAME, current, mems, exs, jp, house.get_prompt_context(), economy_summary=econ
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
        ai_inst = db.query(models.AIInstance).filter(models.AIInstance.owner_id == current_user.id).first()
        chat_history = ai_inst.state_data.get("chat_history", []) if ai_inst and ai_inst.state_data else []

        ai_response = ""
        sf = StreamingTagFilter()
        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=chat_history):
            safe = sf.feed(chunk)
            ai_response += chunk
            if safe:
                await broadcast_to_user(current_user.id, {"type": "ai_chunk", "chunk": safe})

        leftover = sf.flush()
        if leftover:
            await broadcast_to_user(current_user.id, {"type": "ai_chunk", "chunk": leftover})

        for entry in parse_ingat_tags(ai_response):
            name = entry.get("name", "").strip()
            notes = entry.get("notes", "").strip()
            if name:
                state.remember_user(name, notes)

        for c in parse_catat_tags(ai_response):
            journal.add_entry(c["entry"], c["category"])

        ai_response = strip_all_system_tags(ai_response)
        ai_response = re.sub(
            rf"^(?:AI|{re.escape(AI_NAME)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
        ).strip()

        await broadcast_to_user(current_user.id, {"type": "ai_end", "response": ai_response, "source": source})
        if source == "whatsapp" and current_user.id in active_wa_handlers and active_wa_handlers[current_user.id].is_connected:
            active_wa_handlers[current_user.id].send_natural_burst(ai_response)

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

        await asyncio.to_thread(memory.add_memory, current_user.id, "user", user_input)
        await asyncio.to_thread(memory.add_memory, current_user.id, "ai", ai_response)
        state.increase_hunger_by_words(len(ai_response.split()))

    return {"response": ai_response, "mood": state.mood, "state": state.get_state_summary()}


class TopupRequest(BaseModel):
    amount: float
    reason: str = "Top-up via Web"

@app.post("/api/economy/topup")
async def topup(req: TopupRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    economy = EconomyManager(current_user.id, db)
    new_bal = economy.add_balance(req.amount, req.reason)
    await broadcast_to_user(current_user.id, {"type": "economy_state", **economy.get_summary()})
    return {"balance": new_bal, "formatted": economy.get_balance_formatted()}


class CommandRequest(BaseModel):
    command: str
    payload: Optional[str] = None

@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    state = StateManager(current_user.id, db)
    house = HouseManager(current_user.id, db)
    journal = JournalManager(current_user.id, db)
    
    cmd = req.command.lower()
    if cmd == "sleep":
        state.reset_state("sleep")
        house.enqueue_chore("sleep_routine", priority=True)
        journal.add_entry("Ordered to sleep by user via web.", "sleep")
        return {"ok": True, "msg": f"{AI_NAME} is now sleeping 💤"}
    elif cmd == "wake":
        state.reset_state("wake")
        house.enqueue_chore("wake_routine", priority=True)
        journal.add_entry("Woken up by user via web.", "sleep")
        return {"ok": True, "msg": f"{AI_NAME} is awake 🥱"}
    elif cmd == "feed":
        item = req.payload or "mysterious food"
        state.add_food(item.lower().replace(" ", "_"), item, 1, "piece", "🍱")
        await broadcast_to_user(current_user.id, {"type": "inventory_state", **state.get_inventory_state()})
        return {"ok": True, "msg": f"Gave {item} to {AI_NAME}"}
    elif cmd == "status":
        return {"ok": True, "state": state.get_state_summary()}
    else:
        raise HTTPException(400, f"Unknown command: {cmd}")

import jwt
from auth import SECRET_KEY, ALGORITHM

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = None):
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
    if user_id not in active_ws:
        active_ws[user_id] = set()
    active_ws[user_id].add(ws)
    logger.info(f"[WS] ✅ New connection for user '{username}' (id={user_id}). Total sockets: {len(active_ws[user_id])}")

    state = StateManager(user_id, db)
    house = HouseManager(user_id, db)
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
                await broadcast_to_user(user_id, {"type": "user_message", "text": user_text})
                
                db = SessionLocal()
                req = ChatRequest(message=user_text)
                try:
                    result = await chat_endpoint(req, user, db)
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
                    result = await run_command_endpoint(req, user, db)
                    await ws.send_json({"type": "command_result", **result})
                except Exception as e:
                    await ws.send_json({"type": "error", "msg": str(e)})
                finally:
                    db.close()
                    
            elif msg_type == "request_qr":
                master_phone = data.get("master_phone")
                db = SessionLocal()
                ai_inst = db.query(models.AIInstance).filter(models.AIInstance.owner_id == user_id).first()
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
                    await broadcast_to_user(user_id, {"type": "wa_qr", "qr_string": qr_str})
                    
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
        active_ws[user_id].discard(ws)

