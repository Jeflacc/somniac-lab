import asyncio
import math
import logging
import json
import os
import time
import datetime as dt
import os
import time
import datetime as dt

import models
from sqlalchemy.orm import Session

class StateManager:
    def __init__(self, user_id: int, db: Session):
        self.agent_id = agent_id
        self.db = db
        self.load_config()
        
        # Biologics (0.0 means fully satisfied/not present, 1.0 means extreme)
        self.hunger = 0.0
        self.sleepiness = 0.0
        self.libido = 0.0
        self.is_sleeping = False

        # Legacy simple inventory (deprecated — kept for backward compat)
        self.inventory = []

        # New structured inventories
        self.food_inventory: dict = {}  # {item_id: {name, qty, unit, emoji}}
        self.item_inventory: dict = {}  # {item_id: {name, qty, unit, emoji}}

        # Libido Sinusoidal Cycle (72-hour wave, human-like)
        self.libido_phase = 0.0       # 0.0 → 2π, advances over 72h cycle
        self.libido_modifier = 0.0    # interaction delta: -0.5 to +0.5
        
        # Vital signs (derived dynamically, not persisted)
        self._heart_rate = 72   # bpm baseline
        self._breath_rate = 15  # breaths/min baseline
        
        # Base emotions
        self.mood = "neutral" # happy, sad, angry, neutral
        
        # Relationship & Emotions
        self.interaction_count = 0
        self.joy = 0.0
        self.stress = 0.0
        
        # Personality Multipliers (Growth)
        self.irritability_mult = 1.0 
        self.affection_mult = 1.0
        self.laziness_mult = 1.0
        
        self.core_memories = []
        self.known_users = {}  # {name: {"notes": str, "aliases": list}}
        self.last_updated_timestamp = time.time()
        
        # Constraints
        self.max_val = 1.0
        
        # Load from disk
        self.load_state()
        
        # Catch up time if app was closed for a significant period
        current_time = time.time()
        time_elapsed = current_time - self.last_updated_timestamp
        if time_elapsed > 30:
            logging.info(f"App was offline for {time_elapsed:.1f} seconds. Catching up biology state...")
            self.update_state_over_time(seconds_elapsed=time_elapsed)
            
        self._evaluate_mood()

    def load_config(self):
        default_cfg = {
            "hunger_fill_hours": 12.0,
            "sleepiness_fill_hours": 16.0,
            "libido_fill_hours": 24.0,
            "tick_rate_seconds": 300,
            "joy_fade_hours": 1.0,
            "stress_fade_hours": 1.0
        }
        config_path = os.path.join(os.path.dirname(__file__), "biology_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = default_cfg

    def save_state(self):
        self.last_updated_timestamp = time.time()
        
        ai = self.db.query(models.AIAgent).filter(models.AIAgent.id == self.agent_id).first()
        if not ai:
            ai = models.AIAgent(agent_id=self.agent_id)
            self.db.add(ai)
            
        ai.hunger = self.hunger
        ai.sleepiness = self.sleepiness
        ai.libido = self.libido
        ai.is_sleeping = self.is_sleeping
        ai.mood = self.mood
        ai.last_updated = self.last_updated_timestamp
        
        # Save complex data to state_data JSON column
        ai.state_data = {
            "libido_phase": self.libido_phase,
            "libido_modifier": self.libido_modifier,
            "interaction_count": self.interaction_count,
            "joy": self.joy,
            "stress": self.stress,
            "irritability_mult": self.irritability_mult,
            "affection_mult": self.affection_mult,
            "laziness_mult": self.laziness_mult,
            "core_memories": self.core_memories,
            "known_users": self.known_users,
            "inventory": self.inventory,
            "food_inventory": self.food_inventory,
            "item_inventory": self.item_inventory,
        }
        
        self.db.commit()

    def load_state(self):
        ai = self.db.query(models.AIAgent).filter(models.AIAgent.id == self.agent_id).first()
        if not ai:
            return
            
        self.hunger = ai.hunger
        self.sleepiness = ai.sleepiness
        self.libido = ai.libido
        self.is_sleeping = ai.is_sleeping
        self.mood = ai.mood
        self.last_updated_timestamp = ai.last_updated
        
        data = ai.state_data or {}
        
        self.libido_phase = data.get("libido_phase", 0.0)
        self.libido_modifier = data.get("libido_modifier", 0.0)
        self.interaction_count = data.get("interaction_count", 0)
        self.joy = data.get("joy", 0.0)
        self.stress = data.get("stress", 0.0)
        self.irritability_mult = data.get("irritability_mult", 1.0)
        self.affection_mult = data.get("affection_mult", 1.0)
        self.laziness_mult = data.get("laziness_mult", 1.0)
        self.core_memories = data.get("core_memories", [])
        self.known_users = data.get("known_users", {})
        self.inventory = data.get("inventory", [])
        self.food_inventory = data.get("food_inventory", {})
        self.item_inventory = data.get("item_inventory", {})

    @property
    def heart_rate(self) -> int:
        """BPM derived from stress + mood. Range 45–160."""
        base = 72
        if self.is_sleeping:
            return max(45, int(base * 0.65))
        stress_bump    = self.stress    * 50
        hunger_bump    = self.hunger    * 20
        joy_bump       = self.joy       * 15
        libido_bump    = self.libido    * 10
        sleepy_drop    = self.sleepiness * -15
        rate = base + stress_bump + hunger_bump + joy_bump + libido_bump + sleepy_drop
        return max(45, min(160, int(rate)))

    @property
    def breath_rate(self) -> int:
        """Breaths/min derived from stress + sleepiness. Range 6–30."""
        base = 15
        if self.is_sleeping:
            return max(6, int(base * 0.6))
        stress_bump  = self.stress    * 12
        sleepy_drop  = self.sleepiness * -4
        hunger_bump  = self.hunger    * 4
        rate = base + stress_bump + sleepy_drop + hunger_bump
        return max(6, min(30, int(rate)))

    def get_state_summary(self) -> dict:
        return {
            "hunger": round(self.hunger, 2),
            "sleepiness": round(self.sleepiness, 2),
            "libido": round(self.libido, 2),
            "mood": self.mood,
            "relationship": self.get_relationship_status(),
            "core_memories": self.core_memories,
            "known_users": self.known_users,
            "inventory": self.inventory,
            "food_inventory": self.food_inventory,
            "item_inventory": self.item_inventory,
            "heart_rate": self.heart_rate,
            "breath_rate": self.breath_rate,
            "is_sleeping": self.is_sleeping
        }
        
    def increase_familiarity(self):
        self.interaction_count += 1
        self.save_state()

    # ─────────────── Food & Item Inventory ───────────────

    def add_food(self, item_id: str, name: str, qty: float, unit: str, emoji: str):
        """Add food material to inventory."""
        if item_id in self.food_inventory:
            self.food_inventory[item_id]["qty"] += qty
        else:
            self.food_inventory[item_id] = {"name": name, "qty": qty, "unit": unit, "emoji": emoji}
        logging.info(f"[INVENTORY] +{qty} {unit} {emoji} {name}")
        self.save_state()

    def consume_food(self, item_id: str = None, qty: float = 1) -> str:
        """
        Consume food. If item_id=None, take first available.
        Returns name of consumed item, or '' if empty.
        """
        if item_id and item_id in self.food_inventory:
            item = self.food_inventory[item_id]
            consumed_name = item["name"]
            item["qty"] -= qty
            if item["qty"] <= 0:
                del self.food_inventory[item_id]
            self.save_state()
            return consumed_name
        elif not item_id and self.food_inventory:
            first_key = list(self.food_inventory.keys())[0]
            item = self.food_inventory[first_key]
            consumed_name = item["name"]
            item["qty"] -= qty
            if item["qty"] <= 0:
                del self.food_inventory[first_key]
            self.save_state()
            return consumed_name
        return ""

    def can_cook(self) -> bool:
        """True if there's at least 1 food material in food_inventory."""
        return bool(self.food_inventory)

    def get_food_summary(self) -> str:
        """Return brief description of food_inventory."""
        if not self.food_inventory:
            return "No food materials"
        parts = []
        for data in self.food_inventory.values():
            parts.append(f"{data['emoji']} {data['name']} ({data['qty']} {data['unit']})")
        return ", ".join(parts)

    def add_item(self, item_id: str, name: str, qty: float, unit: str, emoji: str):
        """Add item (non-food) to inventory."""
        if item_id in self.item_inventory:
            self.item_inventory[item_id]["qty"] += qty
        else:
            self.item_inventory[item_id] = {"name": name, "qty": qty, "unit": unit, "emoji": emoji}
        logging.info(f"[INVENTORY] +{qty} {unit} {emoji} {name} (item)")
        self.save_state()

    def get_inventory_state(self) -> dict:
        """Inventory snapshot for GUI broadcast."""
        return {
            "food_inventory": self.food_inventory,
            "item_inventory": self.item_inventory,
        }
        
    def get_relationship_status(self) -> str:
        if self.interaction_count < 5:
            return "Stranger (Cold, don't know them yet)"
        elif self.interaction_count < 15:
            return "New Acquaintance (Starting to open up, but still distant)"
        elif self.interaction_count < 30:
            return "Friend (Fun to talk to, vibes are good)"
        else:
            return "Close Friend / Intimate (Very warm, clingy, or blunt)"
    
    def process_interaction_emotion(self, user_text: str):
        """Simplistic emotion tracking to trigger core memory spikes"""
        text = user_text.lower()

        # Talking to user fulfills her need for attention gradually (via modifier)
        self.libido_modifier = max(-0.5, self.libido_modifier - 0.2)
        # Recompute libido after modifier change
        libido_wave = (math.sin(self.libido_phase - math.pi / 2) + 1) / 2
        self.libido = max(0.0, min(1.0, libido_wave * 0.75 + self.libido_modifier * 0.25))
        
        # Stress triggers
        if any(w in text for w in ["stupid", "idiot", "dumb", "ugly", "hate", "stfu", "fuck", "bastard"]):
            self.stress += 0.4
        
        # Joy/Affection triggers
        if any(w in text for w in ["love", "pretty", "handsome", "smart", "great", "thanks", "like", "love you"]):
            self.joy += 0.4
            
        self.check_core_memory_creation(user_text)
        self.save_state()
            
    def check_core_memory_creation(self, context_text: str):
        """If joy or stress spikes past 1.0, create a core memory and permanently alter multipliers."""
        if self.stress >= 1.0:
            memory_text = f"Traumatic/Annoying Experience: Was treated harshly/pressured when hearing phrases related to '{context_text}'. This memory makes the character get angry faster."
            self.core_memories.append(memory_text)
            self.irritability_mult += 0.2
            self.affection_mult = max(0.5, self.affection_mult - 0.1)
            self.stress = 0.0 # reset spike
            logging.info(f"CORE MEMORY FORMED: {memory_text}")
            
        if self.joy >= 1.0:
            memory_text = f"Happy/Memorable Experience: Felt very appreciated/loved during conversation about '{context_text}'. This memory makes the character warmer."
            self.core_memories.append(memory_text)
            self.affection_mult += 0.2
            self.irritability_mult = max(0.5, self.irritability_mult - 0.1)
            self.joy = 0.0 # reset spike
            logging.info(f"CORE MEMORY FORMED: {memory_text}")

    def increase_hunger_by_words(self, word_count: int):
        increment = (word_count / 100) * 0.05
        # irritability multiplier speeds up hunger
        self.hunger = min(self.max_val, self.hunger + (increment * self.irritability_mult))
        self._evaluate_mood()
        self.save_state()

    def check_sleep_schedule(self):
        # 1. Exhaustion forcing sleep
        if self.sleepiness >= 1.0:
            self.is_sleeping = True

        # 3. Scheduled sleep
        is_in_schedule = False
        try:
            sleep_start_str = self.config.get("sleep_schedule_start", "23:00")
            sleep_end_str = self.config.get("sleep_schedule_end", "07:00")
            now_time = dt.datetime.now().time()
            start_time = dt.datetime.strptime(sleep_start_str, "%H:%M").time()
            end_time = dt.datetime.strptime(sleep_end_str, "%H:%M").time()
            
            if start_time <= end_time:
                is_in_schedule = start_time <= now_time <= end_time
            else: # crosses midnight
                is_in_schedule = now_time >= start_time or now_time <= end_time
        except Exception:
            pass
            
        if is_in_schedule:
            self.is_sleeping = True
        
        # 2. Natural Wakeup
        if self.is_sleeping:
            if self.sleepiness <= 0.0 and not is_in_schedule:
                self.is_sleeping = False

    def update_state_over_time(self, seconds_elapsed: float = None):
        if seconds_elapsed is None:
            seconds_elapsed = self.config.get("tick_rate_seconds", 300)
            
        # Calculate rates based on config (fill from 0 to 1 over configured hours)
        h_fill_s = self.config.get("hunger_fill_hours", 6.0) * 3600
        s_fill_s = self.config.get("sleepiness_fill_hours", 16.0) * 3600

        j_fade_s = self.config.get("joy_fade_hours", 1.0) * 3600
        str_fade_s = self.config.get("stress_fade_hours", 1.0) * 3600

        # Increment hunger & sleepiness
        hunger_inc = (seconds_elapsed / h_fill_s) * self.irritability_mult

        if self.is_sleeping:
            sleep_inc = -(seconds_elapsed / (8.0 * 3600))
        else:
            sleep_inc = (seconds_elapsed / s_fill_s) * self.laziness_mult

        self.hunger = min(self.max_val, self.hunger + hunger_inc)
        self.sleepiness = max(0.0, min(self.max_val, self.sleepiness + sleep_inc))

        # ── Libido Sinusoidal Cycle (72-hour wave) ──
        # Phase advances: full 2π in 72 hours
        LIBIDO_CYCLE_SECS = self.config.get("libido_cycle_hours", 72.0) * 3600.0
        phase_inc = (seconds_elapsed / LIBIDO_CYCLE_SECS) * 2.0 * math.pi
        self.libido_phase = (self.libido_phase + phase_inc) % (2.0 * math.pi)

        # Modifier decays toward 0 (half-life ~3 hours)
        decay = max(0.0, 1.0 - (seconds_elapsed / (3.0 * 3600.0)))
        self.libido_modifier = self.libido_modifier * decay

        # Final libido: mostly driven by wave (75%) + modifier (25%)
        libido_wave = (math.sin(self.libido_phase - math.pi / 2.0) + 1.0) / 2.0  # 0.0 – 1.0
        self.libido = max(0.0, min(1.0, libido_wave * 0.75 + self.libido_modifier * 0.25))

        self.check_sleep_schedule()

        # Fade out emotions
        self.joy = max(0.0, self.joy - (seconds_elapsed / j_fade_s))
        self.stress = max(0.0, self.stress - (seconds_elapsed / str_fade_s))

        self.save_state()
        self._evaluate_mood()

    def _evaluate_mood(self):
        if self.hunger > 0.8 or self.sleepiness > 0.8 or self.stress > 0.6:
            self.mood = "angry" 
        elif self.hunger > 0.5 or self.sleepiness > 0.5:
            self.mood = "sad" 
        elif self.libido > 0.7 or self.joy > 0.6:
            self.mood = "happy" 
        else:
            self.mood = "neutral"
            
    def remember_user(self, name: str, notes: str = ""):
        """Permanently store a user's name and optional notes so AI never forgets."""
        key = name.strip().lower()
        existing = self.known_users.get(key, {})
        merged_notes = existing.get("notes", "")
        if notes and notes not in merged_notes:
            merged_notes = (merged_notes + " | " + notes).strip(" | ")
        self.known_users[key] = {
            "display_name": name.strip(),
            "notes": merged_notes
        }
        self.save_state()
        logging.info(f"USER REMEMBERED: {name.strip()} — {merged_notes}")

    def reset_state(self, action: str):
        if action == "eat" or action == "makan":
            self.hunger = 0.0  # Full = reset to 0
        elif action == "sleep" or action == "tidur":
            self.sleepiness = 1.0
            self.is_sleeping = True 
        elif action == "wake" or action == "bangun":
            self.sleepiness = 0.0
            self.is_sleeping = False
        elif action == "relieve":
            self.libido_modifier = max(-0.5, self.libido_modifier - 0.5)
            libido_wave = (math.sin(self.libido_phase - math.pi / 2) + 1) / 2
            self.libido = max(0.0, min(1.0, libido_wave * 0.75 + self.libido_modifier * 0.25))
        self._evaluate_mood()
        self.save_state()
