import json
import os
import time
import logging

ECONOMY_FILE = os.path.join(os.path.dirname(__file__), "economy_state.json")

class EconomyManager:
    """
    Manages AI's money: balance, top-ups, purchases.
    Starting balance: Rp 50.000 (cukup buat belanja groceries beberapa kali).
    """

    def __init__(self, starting_balance: float = 50_000.0):
        self.balance = starting_balance
        self.transaction_history: list[dict] = []
        self.load_state()

    # ─────────────── Public API ───────────────

    def add_balance(self, amount: float, reason: str = "Top-up dari Vathir") -> float:
        """Tambah saldo AI. Returns saldo baru."""
        self.balance += amount
        self._log_tx(f"+Rp {amount:,.0f}", reason, self.balance)
        self.save_state()
        logging.info(f"[ECONOMY] Top-up Rp {amount:,.0f} ({reason})")
        return self.balance

    def spend(self, amount: float, reason: str = "Belanja") -> bool:
        """
        Kurangi saldo. Returns True kalau berhasil, False kalau saldo kurang.
        """
        if self.balance < amount:
            logging.warning(
                f"[ECONOMY] Saldo tidak cukup: Rp {self.balance:,.0f} < Rp {amount:,.0f}"
            )
            return False
        self.balance -= amount
        self._log_tx(f"-Rp {amount:,.0f}", reason, self.balance)
        self.save_state()
        logging.info(f"[ECONOMY] Spent Rp {amount:,.0f} ({reason}) → Sisa: Rp {self.balance:,.0f}")
        return True

    def get_balance_formatted(self) -> str:
        return f"Rp {self.balance:,.0f}".replace(",", ".")

    def get_summary(self) -> dict:
        return {
            "balance": self.balance,
            "balance_formatted": self.get_balance_formatted(),
            "transaction_history": self.transaction_history[-15:],
        }

    # ─────────────── Internals ───────────────

    def _log_tx(self, amount_str: str, reason: str, balance_after: float):
        self.transaction_history.append({
            "time": time.strftime("%H:%M %d/%m"),
            "amount": amount_str,
            "reason": reason,
            "balance_after": balance_after,
        })
        if len(self.transaction_history) > 100:
            self.transaction_history = self.transaction_history[-100:]

    # ─────────────── Persistence ───────────────

    def save_state(self):
        try:
            with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "balance": self.balance,
                    "transaction_history": self.transaction_history,
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[ECONOMY] save_state failed: {e}")

    def load_state(self):
        if not os.path.exists(ECONOMY_FILE):
            return
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.balance = data.get("balance", self.balance)
            self.transaction_history = data.get("transaction_history", [])
            logging.info(f"[ECONOMY] Loaded — Saldo: {self.get_balance_formatted()}")
        except Exception as e:
            logging.error(f"[ECONOMY] load_state failed: {e}")
