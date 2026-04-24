"""
Somniac AI - FastAPI Backend
Main entry point — wraps the Conscious AI engine into a web API with WebSocket streaming.
"""

import os
import sys
import asyncio
import logging
import json
import random
import re
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# ── Load environment ──────────────────────────────────────────────────────────
load_dotenv()

API_PROVIDER  = os.getenv("API_PROVIDER", "groq")
OLLAMA_HOST   = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "llama3")
GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEY_2= os.getenv("GROQ_API_KEY_2", "")
GROQ_MODEL    = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AI_NAME       = os.getenv("AI_NAME", "Evelyn")
MASTER_PHONE  = os.getenv("MASTER_PHONE", "")
FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")

# ── Logging ───────────────────────────────────────────────────────────────────
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

# ── Import core engine modules ────────────────────────────────────────────────
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
    parse_stiker_tag,
    strip_all_system_tags,
)

# ── Global singletons ─────────────────────────────────────────────────────────
state: Optional[StateManager]   = None
memory: Optional[MemoryManager] = None
llm: Optional[LLMController]    = None
journal: Optional[JournalManager] = None
house: Optional[HouseManager]   = None
economy: Optional[EconomyManager] = None
chat_lock: Optional[asyncio.Lock] = None
chat_history: list = []

# Connected WebSocket clients
active_ws: set[WebSocket] = set()


# ── Lifespan: startup / shutdown ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global state, memory, llm, journal, house, economy, chat_lock, chat_history

    logger.info(f"🚀 Menginisialisasi Conscious AI Engine: {AI_NAME}")
    state   = StateManager()
    memory  = MemoryManager()
    journal = JournalManager()
    house   = HouseManager()
    economy = EconomyManager(starting_balance=50_000.0)
    chat_lock = asyncio.Lock()
    chat_history = []

    groq_keys = [k for k in [GROQ_API_KEY, GROQ_API_KEY_2] if k]

    if API_PROVIDER.lower() == "groq":
        llm = LLMController(provider="groq", api_keys=groq_keys, model_name=GROQ_MODEL)
    else:
        llm = LLMController(provider="ollama", model_name=OLLAMA_MODEL, host=OLLAMA_HOST)

    await asyncio.to_thread(memory.init_examples)

    # Start background tasks
    asyncio.create_task(autonomous_loop())
    asyncio.create_task(house_tick_loop())
    asyncio.create_task(state_broadcast_loop())

    logger.info(f"✅ {AI_NAME} Engine ready!")
    yield

    if llm:
        await llm.close()
    logger.info("Backend shutdown complete.")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Somniac AI Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── WebSocket broadcast helper ────────────────────────────────────────────────
async def broadcast(msg: dict):
    dead = set()
    for ws in list(active_ws):
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    active_ws.difference_update(dead)


# ── Background: state broadcast every 1s ─────────────────────────────────────
async def state_broadcast_loop():
    while True:
        await asyncio.sleep(1)
        if state:
            try:
                await broadcast({"type": "state", "state": state.get_state_summary()})
            except Exception:
                pass


# ── Background: house tick every 10s ─────────────────────────────────────────
async def house_tick_loop():
    await asyncio.sleep(5)
    while True:
        await asyncio.sleep(10)
        try:
            if not house:
                continue
            events = house.tick()
            await broadcast({"type": "house_state", **house.get_house_state()})

            if events.get("chore_completed") and events.get("chore_completed_def"):
                chore_def = events["chore_completed_def"]
                journal_text = chore_def.get("journal_text")
                journal_cat  = chore_def.get("journal_category", "kejadian")
                if journal_text:
                    await asyncio.to_thread(journal.add_entry, journal_text, journal_cat)

                on_complete = chore_def.get("on_complete")
                if on_complete == "hunger_reset":
                    state.reset_state("eat")
                elif on_complete == "sleep":
                    state.reset_state("sleep")
                elif on_complete == "wake":
                    state.reset_state("wake")

            if not state.is_sleeping and not house.current_chore_id and not house.chore_queue:
                if state.hunger >= 0.65 and house.needs_eat():
                    house.enqueue_chore("eat")
                elif house.needs_shower():
                    house.enqueue_chore("mandi")
                elif house.needs_laundry():
                    house.enqueue_chore("laundry")
                elif house.boredom > 0.75:
                    house.enqueue_chore(random.choice(["play_console", "watch_tv", "wander"]))

        except Exception as e:
            logger.error(f"[HOUSE TICK] {e}")


# ── Background: autonomous loop every 5min ───────────────────────────────────
async def autonomous_loop():
    await asyncio.sleep(10)
    first = True
    while True:
        if not first:
            await asyncio.sleep(300)
        first = False

        if not state or not llm:
            continue

        was_sleeping = state.is_sleeping
        state.update_state_over_time()
        current = state.get_state_summary()

        trigger = False
        reason  = ""

        if state.is_sleeping and not was_sleeping:
            trigger = True
            reason  = "Sudah masuk jadwal tidurmu. Pamit untuk tidur sekarang."
            journal.add_entry("Mulai waktu tidur. Pamit ke user.", "tidur")
            house.enqueue_chore("sleep_routine", priority=True)
        elif not state.is_sleeping and was_sleeping:
            trigger = True
            reason  = "Kamu baru saja terbangun. Sapa user dengan hangat."
            journal.add_entry("Bangun tidur. Menyapa user.", "tidur")
            house.enqueue_chore("wake_routine", priority=True)
        elif not state.is_sleeping:
            if current["hunger"] > 0.8:
                trigger = True
                reason  = "Lapar banget! Cerita ke user sambil minta makan/masak."
            elif current["sleepiness"] > 0.8:
                trigger = True
                reason  = "Sangat ngantuk, hampir tidak bisa menahan kantuk."

        if trigger and not chat_lock.locked():
            async with chat_lock:
                await broadcast({"type": "ai_thinking", "indicator": "Memikirkan sesuatu..."})
                mem_task = asyncio.to_thread(memory.search_memory, AI_NAME, 1)
                ex_task  = asyncio.to_thread(memory.search_examples, current["mood"])
                mems, exs = await asyncio.gather(mem_task, ex_task)
                jp = await asyncio.to_thread(journal.build_journal_prompt)

                static_p, dynamic_p = build_system_prompt(
                    AI_NAME, current, mems, exs, jp, house.get_prompt_context()
                )
                secret = f"[SISTEM]: Berinisiatiflah memulai obrolan karena {reason}"
                hidden = f"[SISTEM INTERNAL AI]:\n{dynamic_p}\n\n{secret}"

                ai_response = ""
                sf = StreamingTagFilter()
                async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=[]):
                    safe = sf.feed(chunk)
                    ai_response += chunk
                    if safe:
                        await broadcast({"type": "ai_chunk", "chunk": safe})

                leftover = sf.flush()
                if leftover:
                    await broadcast({"type": "ai_chunk", "chunk": leftover})

                ai_response = strip_all_system_tags(ai_response)
                ai_response = re.sub(
                    rf"^(?:AI|{re.escape(AI_NAME)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
                ).strip()
                await broadcast({"type": "ai_end", "response": ai_response, "source": "autonomous"})
                await asyncio.to_thread(memory.add_memory, "ai", ai_response)


# ─────────────────────────────────────────────────────────────────────────────
# REST ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


@app.get("/health")
async def health():
    return {"status": "ok", "ai_name": AI_NAME}


@app.get("/api/state")
async def get_state():
    if not state:
        raise HTTPException(503, "Engine not ready")
    return {
        "state": state.get_state_summary(),
        "house": house.get_house_state() if house else {},
        "economy": economy.get_summary() if economy else {},
    }


@app.get("/api/history")
async def get_history():
    return {"history": chat_history[-40:]}


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """
    Non-streaming REST chat endpoint.
    Returns the full AI response as JSON.
    """
    if not all([state, memory, llm, journal, house]):
        raise HTTPException(503, "Engine not ready")

    user_input = req.message.strip()
    if not user_input:
        raise HTTPException(400, "Empty message")

    if state.is_sleeping:
        return {"response": f"*{AI_NAME} sedang tertidur... sshh*", "mood": state.mood}

    async with chat_lock:
        # Update state
        state.increase_familiarity()
        state.process_interaction_emotion(user_input)
        house.on_interaction()

        detected = extract_name_from_user_message(user_input)
        if detected and detected.lower() not in state.known_users:
            state.remember_user(detected, "Terdeteksi otomatis")

        current = state.get_state_summary()

        mems, exs, jp = await asyncio.gather(
            asyncio.to_thread(memory.search_memory, user_input, 3),
            asyncio.to_thread(memory.search_examples, user_input + " " + current.get("mood", "")),
            asyncio.to_thread(journal.build_journal_prompt),
        )

        econ = economy.get_summary() if economy else None
        if econ:
            econ["food_inventory"] = state.food_inventory

        static_p, dynamic_p = build_system_prompt(
            AI_NAME, current, mems, exs, jp, house.get_prompt_context(), economy_summary=econ
        )

        word_count = len(user_input.split())
        if word_count <= 10:
            length_hint = "[PETUNJUK SISTEM]: Balas singkat, 1-2 kalimat saja."
        elif word_count <= 25:
            length_hint = "[PETUNJUK SISTEM]: Balas secukupnya."
        else:
            length_hint = "[PETUNJUK SISTEM]: Balas ekspresif jika antusias."

        hidden = f"[SISTEM INTERNAL AI]:\n{dynamic_p}\n\n{length_hint}\n\n[PESAN USER BARU]:\n{user_input}"

        ai_response = ""
        sf = StreamingTagFilter()
        async for chunk in llm.generate_response_stream(static_p, user_prompt=hidden, chat_history=chat_history):
            safe = sf.feed(chunk)
            ai_response += chunk
            if safe:
                await broadcast({"type": "ai_chunk", "chunk": safe})

        leftover = sf.flush()
        if leftover:
            await broadcast({"type": "ai_chunk", "chunk": leftover})

        # Parse tags
        for entry in parse_ingat_tags(ai_response):
            name = entry.get("name", "").strip()
            notes = entry.get("notes", "").strip()
            if name:
                state.remember_user(name, notes)

        for c in parse_catat_tags(ai_response):
            await asyncio.to_thread(journal.add_entry, c["entry"], c["category"])

        ai_response = strip_all_system_tags(ai_response)
        ai_response = re.sub(
            rf"^(?:AI|{re.escape(AI_NAME)}|\[AI\])\s*:\s*", "", ai_response.strip(), flags=re.IGNORECASE
        ).strip()

        await broadcast({"type": "ai_end", "response": ai_response, "source": "chat"})

        # Update history
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": ai_response})
        # Trim to ~3000 token
        while sum(len(m["content"]) for m in chat_history) // 4 > 3000 and len(chat_history) > 2:
            chat_history.pop(0)
            chat_history.pop(0)

        await asyncio.to_thread(memory.add_memory, "user", user_input)
        await asyncio.to_thread(memory.add_memory, "ai", ai_response)
        state.increase_hunger_by_words(len(ai_response.split()))

    return {"response": ai_response, "mood": state.mood, "state": state.get_state_summary()}


class TopupRequest(BaseModel):
    amount: float
    reason: str = "Top-up via Web"


@app.post("/api/economy/topup")
async def topup(req: TopupRequest):
    if not economy:
        raise HTTPException(503, "Engine not ready")
    new_bal = economy.add_balance(req.amount, req.reason)
    await broadcast({"type": "economy_state", **economy.get_summary()})
    return {"balance": new_bal, "formatted": economy.get_balance_formatted()}


class CommandRequest(BaseModel):
    command: str  # "sleep" | "wake" | "feed" | "status"
    payload: Optional[str] = None


@app.post("/api/command")
async def run_command_endpoint(req: CommandRequest):
    if not state:
        raise HTTPException(503, "Engine not ready")
    cmd = req.command.lower()
    if cmd == "sleep":
        state.reset_state("sleep")
        house.enqueue_chore("sleep_routine", priority=True)
        journal.add_entry("Disuruh tidur oleh user via web.", "tidur")
        return {"ok": True, "msg": f"{AI_NAME} sekarang tidur 💤"}
    elif cmd == "wake":
        state.reset_state("wake")
        house.enqueue_chore("wake_routine", priority=True)
        journal.add_entry("Dibangunkan oleh user via web.", "tidur")
        return {"ok": True, "msg": f"{AI_NAME} sudah bangun 🥱"}
    elif cmd == "feed":
        item = req.payload or "makanan misterius"
        state.add_food(item.lower().replace(" ", "_"), item, 1, "buah", "🍱")
        await broadcast({"type": "inventory_state", **state.get_inventory_state()})
        return {"ok": True, "msg": f"Memberi {item} ke {AI_NAME}"}
    elif cmd == "status":
        return {"ok": True, "state": state.get_state_summary()}
    else:
        raise HTTPException(400, f"Unknown command: {cmd}")


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    active_ws.add(ws)
    logger.info(f"[WS] New connection. Total: {len(active_ws)}")

    # Send initial state immediately
    if state:
        await ws.send_json({"type": "state", "state": state.get_state_summary()})
    if house:
        await ws.send_json({"type": "house_state", **house.get_house_state()})
    if economy:
        await ws.send_json({"type": "economy_state", **economy.get_summary()})

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue
                # Mirror to all clients
                await broadcast({"type": "user_message", "text": user_text})
                # Process via the chat logic
                req = ChatRequest(message=user_text)
                try:
                    result = await chat_endpoint(req)
                except Exception as e:
                    await ws.send_json({"type": "error", "msg": str(e)})

            elif msg_type == "command":
                cmd = data.get("command", "")
                payload = data.get("payload")
                req = CommandRequest(command=cmd, payload=payload)
                try:
                    result = await run_command_endpoint(req)
                    await ws.send_json({"type": "command_result", **result})
                except Exception as e:
                    await ws.send_json({"type": "error", "msg": str(e)})

    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[WS] Error: {e}")
    finally:
        active_ws.discard(ws)
