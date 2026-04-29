import logging
from datetime import datetime, timedelta

import models
from sqlalchemy.orm import Session

class JournalManager:
    """
    Buku harian AI. Menyimpan catatan harian tentang kejadian, percakapan,
    perasaan, dan aktivitas — terorganisir per tanggal.
    """

    def __init__(self, user_id: int, db: Session):
        self.agent_id = agent_id
        self.db = db
        self._data: dict = {}  # {"2026-04-11": [{"time": "19:30", "entry": "..."}]}
        self._load()

    # ─────────────────────────────────────────────
    # PERSISTENCE
    # ─────────────────────────────────────────────
    def _load(self):
        try:
            records = self.db.query(models.JournalEntry).filter(models.JournalEntry.agent_id == self.agent_id).all()
            self._data = {r.date_str: r.entries for r in records}
        except Exception as e:
            logging.error(f"[Journal] Gagal load: {e}")
            self._data = {}

    def _save(self):
        try:
            for date_str, entries in self._data.items():
                record = self.db.query(models.JournalEntry).filter(
                    models.JournalEntry.agent_id == self.agent_id,
                    models.JournalEntry.date_str == date_str
                ).first()
                if not record:
                    record = models.JournalEntry(agent_id=self.agent_id, date_str=date_str)
                    self.db.add(record)
                record.entries = entries
            self.db.commit()
        except Exception as e:
            logging.error(f"[Journal] Gagal save: {e}")

    # ─────────────────────────────────────────────
    # WRITE
    # ─────────────────────────────────────────────
    def add_entry(self, text: str, category: str = "general"):
        """
        Add an entry to the journal.
        category: "general" | "conversation" | "eat" | "sleep" | "feeling" | "event"
        """
        if not text.strip():
            return

        today = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M")

        if today not in self._data:
            self._data[today] = []

        entry = {
            "time": time_str,
            "category": category,
            "entry": text.strip()
        }
        self._data[today].append(entry)
        self._save()
        logging.info(f"[Journal] [{category}] {time_str}: {text[:80]}...")

    # ─────────────────────────────────────────────
    # READ
    # ─────────────────────────────────────────────
    def get_today_entries(self) -> list[dict]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self._data.get(today, [])

    def get_entries_for_date(self, date_str: str) -> list[dict]:
        """date_str format: '2026-04-11'"""
        return self._data.get(date_str, [])

    def get_recent_entries(self, days: int = 3) -> dict:
        """
        Get entries from last N days.
        Returns: {"2026-04-11": [...], "2026-04-10": [...]}
        """
        result = {}
        today = datetime.now().date()
        for i in range(days):
            d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if d in self._data and self._data[d]:
                result[d] = self._data[d]
        return result

    # ─────────────────────────────────────────────
    # PROMPT INJECTION
    # ─────────────────────────────────────────────
    def build_journal_prompt(self, days: int = 2, max_entries_today: int = 10, max_entries_past: int = 5) -> str:
        """
        Build journal text to be injected into system prompt.
        Today: max_entries_today latest entries.
        Past days: max_entries_past entries per day.
        """
        recent = self.get_recent_entries(days=days + 1)
        if not recent:
            return ""

        today_str = datetime.now().strftime("%Y-%m-%d")

        lines = ["--- MY DIARY ENTRIES ---"]
        lines.append("(These are notes you wrote yourself about what happened. Use them as reference to remember real events.)\n")

        for date_str in sorted(recent.keys(), reverse=True):
            entries = recent[date_str]
            try:
                label_date = datetime.strptime(date_str, "%Y-%m-%d")
                today_dt = datetime.now().date()
                delta = (today_dt - label_date.date()).days
                if delta == 0:
                    label = f"[Today — {label_date.strftime('%d %B %Y')}]"
                    max_e = max_entries_today
                elif delta == 1:
                    label = f"[Yesterday — {label_date.strftime('%d %B %Y')}]"
                    max_e = max_entries_past
                else:
                    label = f"[{label_date.strftime('%d %B %Y')}]"
                    max_e = max(2, max_entries_past - 2)
            except Exception:
                label = f"[{date_str}]"
                max_e = max_entries_past

            lines.append(label)
            # Latest entries
            shown = entries[-max_e:]
            for e in shown:
                cat = e.get("category", "")
                cat_tag = f"[{cat}] " if cat and cat != "general" else ""
                lines.append(f"  • {e['time']} — {cat_tag}{e['entry']}")
            lines.append("")

        return "\n".join(lines)

    def count_today(self) -> int:
        return len(self.get_today_entries())
