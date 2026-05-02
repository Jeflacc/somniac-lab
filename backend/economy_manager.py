import logging
import time

import models
from sqlalchemy.orm import Session

class EconomyManager:
    """
    Manages AI's money: balance, top-ups, purchases.
    Starting balance: Rp 50.000 (cukup buat belanja groceries beberapa kali).
    """

    def __init__(self, agent_id: int, db: Session, starting_balance: float = 50_000.0):
        self.agent_id = agent_id
        self.db = db
        self.balance = starting_balance
        self.transaction_history: list[dict] = []
        self.load_state()

    # ─────────────── Public API ───────────────

    def add_balance(self, amount: float, reason: str = "Top-up from Vathir") -> float:
        """Add AI balance. Returns new balance."""
        self.balance += amount
        self._log_tx(f"+Rp {amount:,.0f}", reason, self.balance)
        self.save_state()
        logging.info(f"[ECONOMY] Top-up Rp {amount:,.0f} ({reason})")
        return self.balance

    def spend(self, amount: float, reason: str = "Shopping") -> bool:
        """
        Deduct balance. Returns True if successful, False if insufficient.
        """
        if self.balance < amount:
            logging.warning(
                f"[ECONOMY] Insufficient balance: Rp {self.balance:,.0f} < Rp {amount:,.0f}"
            )
            return False
        self.balance -= amount
        self._log_tx(f"-Rp {amount:,.0f}", reason, self.balance)
        self.save_state()
        logging.info(f"[ECONOMY] Spent Rp {amount:,.0f} ({reason}) → Remaining: Rp {self.balance:,.0f}")
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
            eco = self.db.query(models.Economy).filter(models.Economy.agent_id == self.agent_id).first()
            if not eco:
                eco = models.Economy(agent_id=self.agent_id)
                self.db.add(eco)
                
            eco.balance = self.balance
            eco.transaction_history = self.transaction_history
            self.db.commit()
        except Exception as e:
            logging.error(f"[ECONOMY] save_state failed: {e}")

    def load_state(self):
        try:
            eco = self.db.query(models.Economy).filter(models.Economy.agent_id == self.agent_id).first()
            if eco:
                self.balance = eco.balance
                self.transaction_history = eco.transaction_history or []
                logging.info(f"[ECONOMY] Loaded — Saldo: {self.get_balance_formatted()}")
        except Exception as e:
            logging.error(f"[ECONOMY] load_state failed: {e}")
