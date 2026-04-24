import logging
import copy
import time
from datetime import datetime, date

import models
from sqlalchemy.orm import Session

# ─────────────── Room & Item Definitions ───────────────
ROOM_DEFINITIONS = {
    "kamar_tidur": {
        "name": "Kamar Tidur", "emoji": "🛏️",
        "items": {
            "kasur":   {"emoji": "🛏️", "state": "idle",   "label": "Kasur"},
            "console": {"emoji": "🎮", "state": "off",    "label": "PS5"},
            "hp":      {"emoji": "📱", "state": "idle",   "label": "HP"},
            "cermin":  {"emoji": "🪞", "state": "idle",   "label": "Cermin"},
            "lemari":  {"emoji": "🚪", "state": "closed", "label": "Lemari Baju"},
        }
    },
    "kamar_mandi": {
        "name": "Kamar Mandi", "emoji": "🚿",
        "items": {
            "shower":      {"emoji": "🚿", "state": "off",  "label": "Shower"},
            "wastafel_km": {"emoji": "🪥", "state": "idle", "label": "Wastafel"},
            "cermin_km":   {"emoji": "🪞", "state": "idle", "label": "Cermin"},
        }
    },
    "dapur": {
        "name": "Dapur", "emoji": "🍳",
        "items": {
            "kompor":    {"emoji": "🍳", "state": "off",    "label": "Kompor"},
            "piring":    {"emoji": "🍽️", "state": "bersih", "label": "Piring"},
            "wastafel":  {"emoji": "🪣", "state": "off",    "label": "Wastafel"},
            "kulkas":    {"emoji": "🧊", "state": "idle",   "label": "Kulkas"},
        }
    },
    "ruang_tamu": {
        "name": "Ruang Tamu", "emoji": "🛋️",
        "items": {
            "tv":      {"emoji": "📺", "state": "off",  "label": "TV"},
            "sofa":    {"emoji": "🛋️", "state": "idle", "label": "Sofa"},
            "tanaman": {"emoji": "🪴", "state": "idle", "label": "Tanaman"},
        }
    },
    "area_cuci": {
        "name": "Area Cuci", "emoji": "🫧",
        "items": {
            "mesin_cuci": {"emoji": "🫧", "state": "off",    "label": "Mesin Cuci"},
            "jemuran":    {"emoji": "👗", "state": "kosong", "label": "Jemuran"},
        }
    }
}

# ─────────────── Chore Definitions ───────────────
CHORE_DEFINITIONS = {
    "eat": {
        "name": "Masak & Makan", "emoji": "🍳",
        "steps": [
            {"label": "Pergi ke dapur",             "room": "dapur", "duration": 12},
            {"label": "Ambil bahan dari kulkas",    "room": "dapur", "duration": 15, "item": "kulkas",   "item_state": "open"},
            {"label": "Mulai masak",                "room": "dapur", "duration": 60, "item": "kompor",   "item_state": "cooking"},
            {"label": "Siapkan piring, matiin kompor", "room": "dapur", "duration": 15, "item": "piring", "item_state": "dipakai"},
            {"label": "Makan",                      "room": "dapur", "duration": 90, "item": "kompor",   "item_state": "off"},
            {"label": "Cuci piring",                "room": "dapur", "duration": 40, "item": "wastafel", "item_state": "running"},
            {"label": "Bereskan dapur",             "room": "dapur", "duration": 12, "item": "piring",   "item_state": "bersih"},
        ],
        "on_complete": "hunger_reset",
        "journal_text": "Masak sendiri dan makan, lumayan hasilnya",
        "journal_category": "makan"
    },
    "mandi": {
        "name": "Mandi", "emoji": "🚿",
        "steps": [
            {"label": "Ke kamar mandi",            "room": "kamar_mandi", "duration": 10},
            {"label": "Nyalain shower",             "room": "kamar_mandi", "duration": 10, "item": "shower", "item_state": "on"},
            {"label": "Mandi",                      "room": "kamar_mandi", "duration": 120, "item": "shower", "item_state": "running"},
            {"label": "Matiin shower, keringin",    "room": "kamar_mandi", "duration": 15, "item": "shower", "item_state": "off"},
        ],
        "on_complete": "shower_done",
        "journal_text": "Udah mandi, seger banget",
        "journal_category": "kejadian"
    },
    "ganti_baju": {
        "name": "Ganti Baju", "emoji": "👗",
        "steps": [
            {"label": "Ke kamar tidur",                 "room": "kamar_tidur", "duration": 10},
            {"label": "Buka lemari, pilih baju",        "room": "kamar_tidur", "duration": 20, "item": "lemari", "item_state": "open"},
            {"label": "Ganti baju",                     "room": "kamar_tidur", "duration": 25, "item": "lemari", "item_state": "closed"},
        ],
        "on_complete": "clothes_dirty",
        "journal_text": "Ganti baju, sekarang pake baju bersih",
        "journal_category": "kejadian"
    },
    "cuci_piring": {
        "name": "Cuci Piring", "emoji": "🧹",
        "steps": [
            {"label": "Ke dapur",                  "room": "dapur", "duration": 10},
            {"label": "Bilas piring",               "room": "dapur", "duration": 15, "item": "wastafel", "item_state": "on"},
            {"label": "Cuci piring",                "room": "dapur", "duration": 50, "item": "wastafel", "item_state": "running"},
            {"label": "Piring udah bersih",         "room": "dapur", "duration": 10, "item": "piring",   "item_state": "bersih"},
        ],
        "journal_text": "Cuci piring selesai, dapur bersih lagi",
        "journal_category": "kejadian"
    },
    "sleep_routine": {
        "name": "Rutinitas Tidur", "emoji": "🌙",
        "steps": [
            {"label": "Ke kamar mandi buat mandi malem", "room": "kamar_mandi", "duration": 10},
            {"label": "Mandi malem",                     "room": "kamar_mandi", "duration": 90, "item": "shower",  "item_state": "running"},
            {"label": "Keringkan badan",                 "room": "kamar_mandi", "duration": 15, "item": "shower",  "item_state": "off"},
            {"label": "Ke kamar, ganti piyama",          "room": "kamar_tidur", "duration": 20, "item": "lemari",  "item_state": "closed"},
            {"label": "Rebahan di kasur",                "room": "kamar_tidur", "duration": 15, "item": "kasur",   "item_state": "sleeping"},
        ],
        "on_complete": "sleep",
        "journal_text": "Mandi malem, ganti piyama, terus tidur",
        "journal_category": "tidur"
    },
    "wake_routine": {
        "name": "Rutinitas Bangun", "emoji": "☀️",
        "steps": [
            {"label": "Bangun dari kasur",          "room": "kamar_tidur", "duration": 20, "item": "kasur",      "item_state": "idle"},
            {"label": "Cuci muka",                  "room": "kamar_mandi", "duration": 30, "item": "wastafel_km","item_state": "running"},
            {"label": "Ganti baju pagi",            "room": "kamar_tidur", "duration": 25, "item": "lemari",     "item_state": "closed"},
        ],
        "on_complete": "wake",
        "journal_text": "Bangun, cuci muka, ganti baju, siap mulai hari",
        "journal_category": "tidur"
    },
    "laundry": {
        "name": "Cuci Baju", "emoji": "👕",
        "steps": [
            {"label": "Kumpulin baju kotor",         "room": "kamar_tidur", "duration": 15},
            {"label": "Ke area cuci",                "room": "area_cuci",   "duration": 10},
            {"label": "Masukin ke mesin cuci",       "room": "area_cuci",   "duration": 15, "item": "mesin_cuci", "item_state": "running"},
            {"label": "Tunggu mesin cuci",           "room": "area_cuci",   "duration": 90, "item": "mesin_cuci", "item_state": "running"},
            {"label": "Jemur baju",                  "room": "area_cuci",   "duration": 25, "item": "jemuran",    "item_state": "ada_baju"},
            {"label": "Matiin mesin cuci",           "room": "area_cuci",   "duration": 8,  "item": "mesin_cuci", "item_state": "off"},
        ],
        "on_complete": "laundry_done",
        "journal_text": "Cuci baju selesai, udah dijemur nih",
        "journal_category": "kejadian"
    },

    # ── check_wa: flow baru yang realistis ──
    # Step 0: Ambil HP           → masuk kamar, buka HP
    # Step 1: Buka WA, baca      → MARK READ di sini
    # Step 2: Mikirin balesan... → trigger LLM ke wa_ready_queue + set_typing(True)
    # Step 3: Ngetik balesan...  → BLOK sampai LLM selesai & pesan terkirim (wait_for_reply_sent)
    # Step 4: Pegang HP, nunggu  → tahan HP 60 dtk; kalau Vathir balas, loncat balik ke step 2
    # Step 5: Letakkan HP        → selesai
    "check_wa": {
        "name": "Cek WhatsApp", "emoji": "📱",
        "mark_read_on_step": 1,   # mark_read dipanggil saat step 1 selesai
        "wa_reply_on_step": 2,    # LLM di-trigger saat step 2 selesai
        "wa_hold_step": 4,        # index step "pegang HP, nunggu"
        "steps": [
            {"label": "Ke kamar, ambil HP",         "room": "kamar_tidur", "duration": 10, "item": "hp", "item_state": "open"},
            {"label": "Buka WhatsApp, baca pesan",  "room": "kamar_tidur", "duration": 10, "item": "hp", "item_state": "texting"},
            {"label": "Mikirin balesan...",          "room": "kamar_tidur", "duration": 5,  "item": "hp", "item_state": "texting"},
            {"label": "Lagi ngetik balesan...",      "room": "kamar_tidur", "duration": 5,  "item": "hp", "item_state": "texting",
             "wait_for_reply_sent": True},  # step ini BLOK sampai wa_reply_sent=True
            {"label": "Pegang HP, nunggu balesan",  "room": "kamar_tidur", "duration": 60, "item": "hp", "item_state": "texting"},
            {"label": "Letakkan HP",                "room": "kamar_tidur", "duration": 5,  "item": "hp", "item_state": "idle"},
        ],
        "journal_category": "percakapan"
    },

    "play_console": {
        "name": "Main Game Console", "emoji": "🎮",
        "steps": [
            {"label": "Ke kamar, ambil controller",  "room": "kamar_tidur", "duration": 10},
            {"label": "Hidupkan PS5",                "room": "kamar_tidur", "duration": 15, "item": "console", "item_state": "on"},
            {"label": "Seru-seruan main game",       "room": "kamar_tidur", "duration": 300, "item": "console", "item_state": "playing"},
            {"label": "Selesai main, matiin console","room": "kamar_tidur", "duration": 10, "item": "console", "item_state": "off"},
        ],
        "on_complete": "boredom_reduce",
        "send_wa_notif": True,
        "wa_notif_text": "btw gw lagi main ps5 nih, bosen nunggu lu bales 😤🎮",
        "journal_text": "Main PS5 sendirian buat ngilangin bosen",
        "journal_category": "kejadian"
    },
    "watch_tv": {
        "name": "Nonton TV", "emoji": "📺",
        "steps": [
            {"label": "Ke ruang tamu",               "room": "ruang_tamu", "duration": 10},
            {"label": "Nyalain TV, duduk di sofa",   "room": "ruang_tamu", "duration": 10, "item": "tv", "item_state": "on"},
            {"label": "Nonton TV",                   "room": "ruang_tamu", "duration": 180, "item": "tv", "item_state": "on"},
            {"label": "Matiin TV",                   "room": "ruang_tamu", "duration": 5,  "item": "tv", "item_state": "off"},
        ],
        "on_complete": "boredom_reduce",
        "journal_text": "Nonton TV di ruang tamu buat ngusir bosen",
        "journal_category": "kejadian"
    },
    "wander": {
        "name": "Jalan-Jalan", "emoji": "🚶",
        "steps": [
            {"label": "Jalan ke ruang tamu",  "room": "ruang_tamu",  "duration": 30},
            {"label": "Intip isi dapur",       "room": "dapur",       "duration": 20},
            {"label": "Balik ke kamar",        "room": "kamar_tidur", "duration": 20},
        ],
        "journal_text": "Jalan-jalan keliling rumah ga ada kerjaan, iseng aja",
        "journal_category": "kejadian"
    },

    # ── Belanja online: AI beli bahan / barang lewat HP/laptop ──
    "online_shopping": {
        "name": "Belanja Online", "emoji": "🛒",
        "steps": [
            {"label": "Ambil HP, buka aplikasi belanja",  "room": "kamar_tidur", "duration": 15, "item": "hp", "item_state": "open"},
            {"label": "Browsing toko online...",           "room": "kamar_tidur", "duration": 25, "item": "hp", "item_state": "texting"},
            {"label": "Milih-milih produk yang mau dibeli","room": "kamar_tidur", "duration": 30, "item": "hp", "item_state": "texting"},
            {"label": "Checkout & bayar!",                 "room": "kamar_tidur", "duration": 15, "item": "hp", "item_state": "texting"},
            {"label": "Nunggu kurir dateng...",            "room": "kamar_tidur", "duration": 90, "item": "hp", "item_state": "idle"},
        ],
        "on_complete": "shopping_done",
        "journal_text": "Belanja online, barang udah diterima dari kurir",
        "journal_category": "kejadian"
    },
}


class HouseManager:
    """
    Manages the physical space, inventory interactions, and chore queues.
    """

    def __init__(self, user_id: int, db: Session):
        self.user_id = user_id
        self.db = db
        self.rooms = copy.deepcopy(ROOM_DEFINITIONS)
        self.current_room = "kamar_tidur"
        self.current_chore_id = None
        self.current_chore = None
        self.chore_step_index = 0
        self.step_start_time = time.time()
        self.chore_queue = []
        self.wa_pending = []
        self.chore_history = []
        self.boredom = 0.0
        self.last_interaction_time = time.time()
        self._new_chore_started = False

        # ── WA reply sync flag ──
        self.wa_reply_sent = False
        self._mark_read_pending = None

        # ── Hygiene & Laundry tracking ──
        self.dirty_laundry_count = 0
        self.showers_today = 0
        self.last_shower_date = ""
        self.last_shower_time = 0.0
        self.last_eat_time = 0.0

        # ── Shopping cart: items to deliver when online_shopping chore completes ──
        # Format: list of {"id", "name", "qty", "unit", "emoji", "cat": "food"|"item"}
        self.shopping_cart: list[dict] = []

        self.load_state()

    # ─────────────── Public API ───────────────

    def enqueue_chore(self, chore_id: str, priority: bool = False, data=None):
        """Add a chore to queue. Skip duplicates (except check_wa handled separately)."""
        if chore_id not in CHORE_DEFINITIONS:
            logging.warning(f"[HOUSE] Unknown chore: {chore_id}")
            return

        if chore_id == "check_wa":
            already_queued = any(q["id"] == "check_wa" for q in self.chore_queue)
            if already_queued or self.current_chore_id == "check_wa":
                return
        else:
            if any(q["id"] == chore_id for q in self.chore_queue):
                return
            if self.current_chore_id == chore_id:
                return

        item = {"id": chore_id, "data": data}
        if priority:
            self.chore_queue.insert(0, item)
        else:
            self.chore_queue.append(item)
        self.save_state()
        logging.info(f"[HOUSE] Queued chore: {chore_id} (priority={priority})")

    def enqueue_wa(self, user_input: str, wa_message):
        """
        Queue an incoming WA message for delayed processing.

        Jika AI sedang di step 'pegang HP, nunggu balesan' (wa_hold_step),
        langsung lompat balik ke step baca pesan — biar konversasi nyambung
        tanpa perlu letakkan HP dulu.
        """
        self.wa_pending.append({
            "user_input": user_input,
            "wa_message": wa_message,
            "queued_at": time.time()
        })
        self.last_interaction_time = time.time()
        self.boredom = max(0.0, self.boredom - 0.2)

        # ── Conversation hold jump-back ──
        # Kalau lagi di step "Pegang HP, nunggu balesan" → jangan letakkan HP,
        # langsung loncat balik ke step 2 "Mikirin balesan" supaya balas sekalian.
        hold_step = self.current_chore.get("wa_hold_step", -1) if self.current_chore else -1
        if (self.current_chore_id == "check_wa"
                and self.chore_step_index == hold_step):
            logging.info("[HOUSE] Vathir balas saat hold step → loncat balik ke step 2 (baca pesan)")
            self.chore_step_index = 2          # "Mikirin balesan..."
            self.step_start_time = time.time()
            self.wa_reply_sent = False
            # Mark read langsung untuk pesan baru (karena step 1 gak terulang)
            self._mark_read_pending = wa_message
        else:
            self.enqueue_chore("check_wa", priority=True)

        self.save_state()
        logging.info(f"[HOUSE] WA queued: '{user_input[:40]}...'")

    def notify_wa_reply_sent(self):
        """
        Dipanggil oleh main.py setelah LLM selesai dan pesan WA terkirim.
        Membuka blokir step 'wait_for_reply_sent' di chore check_wa.
        """
        self.wa_reply_sent = True
        logging.info("[HOUSE] wa_reply_sent = True → step ngetik bisa lanjut")

    def on_interaction(self):
        """Call on any user interaction to reduce boredom."""
        self.last_interaction_time = time.time()
        self.boredom = max(0.0, self.boredom - 0.3)

    # ─────────────── Lifecycle helpers ───────────────

    def _reset_shower_count_if_new_day(self):
        today_str = date.today().isoformat()
        if self.last_shower_date != today_str:
            self.showers_today = 0
            self.last_shower_date = today_str

    def _on_shower_done(self):
        self._reset_shower_count_if_new_day()
        self.showers_today += 1
        self.last_shower_time = time.time()
        self.dirty_laundry_count += 1
        logging.info(f"[HOUSE] Mandi ke-{self.showers_today} hari ini. Cucian: {self.dirty_laundry_count}")

    def _on_clothes_changed(self):
        self.dirty_laundry_count += 1
        logging.info(f"[HOUSE] Ganti baju. Cucian kotor: {self.dirty_laundry_count}")

    def _on_laundry_done(self):
        self.dirty_laundry_count = 0
        logging.info("[HOUSE] Cucian selesai! Semua bersih.")

    def get_laundry_mood_penalty(self) -> float:
        if self.dirty_laundry_count <= 3:
            return 0.0
        elif self.dirty_laundry_count <= 7:
            return 0.1 * (self.dirty_laundry_count - 3)
        else:
            return min(0.6, 0.4 + 0.05 * (self.dirty_laundry_count - 8))

    def needs_shower(self) -> bool:
        self._reset_shower_count_if_new_day()
        if self.showers_today >= 2:
            return False
        return (time.time() - self.last_shower_time) >= 6 * 3600

    def needs_eat(self) -> bool:
        return (time.time() - self.last_eat_time) >= 3 * 3600

    def needs_laundry(self) -> bool:
        return self.dirty_laundry_count >= 8

    @property
    def is_holding_phone(self) -> bool:
        """True saat step chore aktif melibatkan HP (state != idle)."""
        if not self.current_chore or self.chore_step_index >= len(self.current_chore["steps"]):
            return False
        step = self.current_chore["steps"][self.chore_step_index]
        return step.get("item") == "hp" and step.get("item_state", "idle") != "idle"

    # ─────────────── Tick ───────────────

    def tick(self) -> dict:
        """
        Advance house state by one tick (every 10 seconds).
        Returns events dict consumed by house_tick_loop in main.py.
        """
        events = {
            "wa_reply_ready": False,
            "wa_data": None,
            "chore_completed": None,
            "chore_completed_def": None,
            "new_chore_started": None,
            "wa_notif_text": None,
            "laundry_mood_penalty": self.get_laundry_mood_penalty(),
            # mark_read event: emitted when step mark_read_on_step completes
            # OR immediately from enqueue_wa jump-back
            "mark_read_wa_message": None,
            "holding_phone": self.is_holding_phone,
        }

        now = time.time()

        # Flush pending mark_read dari jump-back conversation hold
        if self._mark_read_pending is not None:
            events["mark_read_wa_message"] = self._mark_read_pending
            self._mark_read_pending = None

        # ── Boredom tick ──
        if self.current_chore_id is None:
            boredom_inc = 10.0 / (2.0 * 3600.0)
            self.boredom = min(1.0, self.boredom + boredom_inc)
        else:
            self.boredom = max(0.0, self.boredom - 0.001)

        # ── Start next chore if idle ──
        if self.current_chore_id is None and self.chore_queue:
            next_item = self.chore_queue.pop(0)
            cid = next_item["id"]
            if cid not in CHORE_DEFINITIONS:
                self.save_state()
                return events

            self.current_chore_id = cid
            self.current_chore = CHORE_DEFINITIONS[cid]
            self.chore_step_index = 0
            self.step_start_time = now
            first_step = self.current_chore["steps"][0]
            self.current_room = first_step["room"]
            self._apply_item_state(first_step)

            events["new_chore_started"] = cid
            if self.current_chore.get("send_wa_notif") and self.current_chore.get("wa_notif_text"):
                events["wa_notif_text"] = self.current_chore["wa_notif_text"]

            logging.info(f"[HOUSE] Chore started: {self.current_chore['name']}")

        # ── Advance active chore ──
        if self.current_chore_id and self.current_chore:
            steps = self.current_chore["steps"]
            if self.chore_step_index < len(steps):
                current_step = steps[self.chore_step_index]
                time_in_step = now - self.step_start_time

                if time_in_step >= current_step["duration"]:

                    # ── wait_for_reply_sent BLOCKER ──
                    # Kalau step ini butuh nunggu LLM selesai kirim, jangan advance dulu
                    if current_step.get("wait_for_reply_sent") and not self.wa_reply_sent:
                        # Tetap di step ini — tunggu notify_wa_reply_sent() dipanggil
                        pass

                    else:
                        # ── Mark read event ──
                        mark_read_step = self.current_chore.get("mark_read_on_step", -1)
                        if mark_read_step == self.chore_step_index and self.wa_pending:
                            # Peek (jangan pop) — data masih dibutuhkan saat wa_reply_on_step
                            events["mark_read_wa_message"] = self.wa_pending[0].get("wa_message")

                        # ── WA reply trigger ──
                        wa_reply_step = self.current_chore.get("wa_reply_on_step", -1)
                        if wa_reply_step == self.chore_step_index and self.wa_pending:
                            wa_data = self.wa_pending.pop(0)
                            events["wa_reply_ready"] = True
                            events["wa_data"] = wa_data

                        # Reset wait flag setelah keluar dari step blocker
                        if current_step.get("wait_for_reply_sent"):
                            self.wa_reply_sent = False

                        # Advance ke step berikutnya
                        self.chore_step_index += 1
                        self.step_start_time = now

                        if self.chore_step_index >= len(steps):
                            # Chore complete!
                            completed_id = self.current_chore_id
                            completed_def = dict(self.current_chore)
                            events["chore_completed"] = completed_id
                            events["chore_completed_def"] = completed_def

                            ts = datetime.now().strftime("%H:%M")
                            self.chore_history.append({
                                "chore_id": completed_id,
                                "name": completed_def.get("name", completed_id),
                                "emoji": completed_def.get("emoji", "✅"),
                                "time": ts,
                                "journal": completed_def.get("journal_text", f"Selesai {completed_def.get('name')}"),
                                "journal_category": completed_def.get("journal_category", "kejadian"),
                                "on_complete": completed_def.get("on_complete")
                            })
                            if len(self.chore_history) > 20:
                                self.chore_history = self.chore_history[-20:]

                            # Apply completion effects
                            on_complete = completed_def.get("on_complete")
                            if on_complete == "boredom_reduce":
                                self.boredom = max(0.0, self.boredom - 0.5)
                            elif on_complete == "shower_done":
                                self._on_shower_done()
                            elif on_complete == "clothes_dirty":
                                self._on_clothes_changed()
                            elif on_complete == "laundry_done":
                                self._on_laundry_done()
                            elif on_complete == "hunger_reset":
                                self.last_eat_time = time.time()

                            # Reset
                            self.current_chore_id = None
                            self.current_chore = None
                            self.chore_step_index = 0
                            self.wa_reply_sent = False

                            # Re-queue check_wa jika masih ada WA yang belum dibalas
                            if completed_id == "check_wa" and self.wa_pending:
                                self.enqueue_chore("check_wa", priority=True)

                        else:
                            next_step = steps[self.chore_step_index]
                            self.current_room = next_step["room"]
                            self._apply_item_state(next_step)

        self.save_state()
        return events

    # ─────────────── State Queries ───────────────

    def get_house_state(self) -> dict:
        if self.current_chore_id and self.current_chore:
            steps_def = self.current_chore["steps"]
            total_steps = len(steps_def)
            step_label = ""
            step_progress = 0.0
            if self.chore_step_index < total_steps:
                current_step = steps_def[self.chore_step_index]
                step_label = current_step["label"]
                time_in_step = time.time() - self.step_start_time
                step_progress = min(1.0, time_in_step / max(1, current_step["duration"]))
            steps_labels = [s["label"] for s in steps_def]
        else:
            total_steps = 0
            step_label = "Santai aja di rumah"
            step_progress = 0.0
            steps_labels = []

        lc = self.dirty_laundry_count
        if lc == 0:
            laundry_label = "Bersih semua ✅"
        elif lc <= 3:
            laundry_label = f"{lc} helai kotor 👕"
        elif lc <= 7:
            laundry_label = f"{lc} helai kotor — mulai numpuk ⚠️"
        else:
            laundry_label = f"{lc} helai kotor — PARAH 😤"

        return {
            "current_room": self.current_room,
            "room_name": ROOM_DEFINITIONS.get(self.current_room, {}).get("name", self.current_room),
            "current_chore_id": self.current_chore_id,
            "current_chore_name": self.current_chore["name"] if self.current_chore else None,
            "current_chore_emoji": self.current_chore["emoji"] if self.current_chore else None,
            "chore_step_index": self.chore_step_index,
            "chore_total_steps": total_steps,
            "chore_step_label": step_label,
            "chore_step_progress": round(step_progress, 2),
            "chore_steps": steps_labels,
            "chore_queue": [
                {"id": q["id"], "name": CHORE_DEFINITIONS[q["id"]]["name"], "emoji": CHORE_DEFINITIONS[q["id"]]["emoji"]}
                for q in self.chore_queue if q["id"] in CHORE_DEFINITIONS
            ],
            "rooms": {
                room_id: {
                    "name": room_data["name"],
                    "emoji": room_data["emoji"],
                    "items": {
                        item_id: {
                            "emoji": item["emoji"],
                            "state": item["state"],
                            "label": item["label"]
                        }
                        for item_id, item in room_data["items"].items()
                    }
                }
                for room_id, room_data in self.rooms.items()
            },
            "chore_history": self.chore_history[-8:],
            "boredom": round(self.boredom, 2),
            "wa_pending_count": len(self.wa_pending),
            "dirty_laundry_count": self.dirty_laundry_count,
            "laundry_label": laundry_label,
            "showers_today": self.showers_today,
            "laundry_mood_penalty": round(self.get_laundry_mood_penalty(), 2),
        }

    def get_prompt_context(self) -> str:
        room_name = ROOM_DEFINITIONS.get(self.current_room, {}).get("name", self.current_room)

        if self.current_chore_id and self.current_chore:
            steps_def = self.current_chore["steps"]
            step_label = ""
            if self.chore_step_index < len(steps_def):
                step_label = steps_def[self.chore_step_index]["label"]
            chore_info = f"Sedang: {self.current_chore['name']} — {step_label} (step {self.chore_step_index + 1}/{len(steps_def)})"
        else:
            chore_info = "Sedang: Idle / Tidak ada kegiatan"

        queue_str = ""
        if self.chore_queue:
            queue_names = [
                CHORE_DEFINITIONS[q["id"]]["name"]
                for q in self.chore_queue if q["id"] in CHORE_DEFINITIONS
            ]
            queue_str = f"\n- Antrian berikutnya: {', '.join(queue_names)}"

        hp_state = self.rooms.get("kamar_tidur", {}).get("items", {}).get("hp", {}).get("state", "idle")
        console_state = self.rooms.get("kamar_tidur", {}).get("items", {}).get("console", {}).get("state", "off")

        boredom_note = ""
        if self.boredom > 0.8:
            boredom_note = "\n- TINGKAT KEBOSANAN: SANGAT TINGGI — kamu bosen parah banget nih"
        elif self.boredom > 0.5:
            boredom_note = "\n- Tingkat Kebosanan: Lumayan bosen, pengen ada kerjaan"

        self._reset_shower_count_if_new_day()
        hygiene_note = f"\n- Mandi hari ini: {self.showers_today}x"
        if self.showers_today == 0:
            hygiene_note += " (belum mandi sama sekali hari ini!)"
        elif self.showers_today == 1:
            hygiene_note += " (baru 1x, masih kurang 1x lagi)"

        laundry_note = ""
        lc = self.dirty_laundry_count
        if lc >= 8:
            laundry_note = f"\n- CUCIAN NUMPUK PARAH: {lc} helai baju kotor — bikin stress dan bad mood!"
        elif lc >= 4:
            laundry_note = f"\n- Cucian mulai numpuk: {lc} helai baju kotor"

        return (
            f"--- POSISI & AKTIVITAS DI RUMAH (REAL-TIME) ---\n"
            f"- Lokasi: {room_name}\n"
            f"- {chore_info}{queue_str}\n"
            f"- Status HP: {hp_state}  |  Console PS5: {console_state}"
            f"{boredom_note}"
            f"{hygiene_note}"
            f"{laundry_note}"
        )

    # ─────────────── Internal Helpers ───────────────

    def _apply_item_state(self, step: dict):
        item_id = step.get("item")
        item_state = step.get("item_state")
        if item_id and item_state:
            room = self.rooms.get(self.current_room, {})
            items = room.get("items", {})
            if item_id in items:
                items[item_id]["state"] = item_state

    # ─────────────── Persistence ───────────────

    def save_state(self):
        data = {
            "current_room": self.current_room,
            "current_chore_id": self.current_chore_id,
            "chore_step_index": self.chore_step_index,
            "step_start_time": self.step_start_time,
            "chore_queue": self.chore_queue,
            "chore_history": self.chore_history,
            "boredom": self.boredom,
            "last_interaction_time": self.last_interaction_time,
            "wa_reply_sent": self.wa_reply_sent,
            "dirty_laundry_count": self.dirty_laundry_count,
            "showers_today": self.showers_today,
            "last_shower_date": self.last_shower_date,
            "last_shower_time": self.last_shower_time,
            "last_eat_time": self.last_eat_time,
            "shopping_cart": self.shopping_cart,
            "item_states": {
                room_id: {
                    item_id: item["state"]
                    for item_id, item in room_data["items"].items()
                }
                for room_id, room_data in self.rooms.items()
            }
        }
        try:
            house = self.db.query(models.HouseState).filter(models.HouseState.owner_id == self.user_id).first()
            if not house:
                house = models.HouseState(owner_id=self.user_id)
                self.db.add(house)
                
            house.current_chore_id = self.current_chore_id
            house.current_chore_start_time = self.step_start_time
            house.chore_queue = self.chore_queue
            house.rooms_data = data
            self.db.commit()
        except Exception as e:
            logging.error(f"[HOUSE] save_state failed: {e}")

    def load_state(self):
        try:
            house = self.db.query(models.HouseState).filter(models.HouseState.owner_id == self.user_id).first()
            if not house:
                return
                
            data = house.rooms_data or {}

            self.current_room = data.get("current_room", "kamar_tidur")
            cid = data.get("current_chore_id")
            if cid and cid in CHORE_DEFINITIONS:
                self.current_chore_id = cid
                self.current_chore = CHORE_DEFINITIONS[cid]
            else:
                self.current_chore_id = None
                self.current_chore = None

            self.chore_step_index = data.get("chore_step_index", 0)
            self.step_start_time = data.get("step_start_time", time.time())
            self.chore_queue = data.get("chore_queue", [])
            self.chore_history = data.get("chore_history", [])
            self.boredom = data.get("boredom", 0.0)
            self.last_interaction_time = data.get("last_interaction_time", time.time())
            # On restart, treat as if reply was already sent to avoid stale block
            self.wa_reply_sent = data.get("wa_reply_sent", True)

            self.dirty_laundry_count = data.get("dirty_laundry_count", 0)
            self.showers_today = data.get("showers_today", 0)
            self.last_shower_date = data.get("last_shower_date", "")
            self.last_shower_time = data.get("last_shower_time", 0.0)
            self.last_eat_time = data.get("last_eat_time", 0.0)
            self.shopping_cart = data.get("shopping_cart", [])

            saved_items = data.get("item_states", {})
            for room_id, items in saved_items.items():
                if room_id in self.rooms:
                    for item_id, state in items.items():
                        if item_id in self.rooms[room_id]["items"]:
                            self.rooms[room_id]["items"][item_id]["state"] = state

            logging.info("[HOUSE] State loaded from DB.")
        except Exception as e:
            logging.error(f"[HOUSE] load_state failed: {e}")
