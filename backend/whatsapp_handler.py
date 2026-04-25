import os
import asyncio
import threading
from dotenv import load_dotenv

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, QREv
from neonize.utils import build_jid
from neonize.utils.enum import Presence, ChatPresence, ReceiptType, ChatPresenceMedia

load_dotenv(override=True)
STICKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "stickers"))
os.makedirs(STICKER_DIR, exist_ok=True)

class WhatsAppHandler:
    def __init__(self, user_id: int, master_phone: str, in_queue: asyncio.Queue, main_loop: asyncio.AbstractEventLoop, qr_callback=None):
        self.user_id = user_id
        self.in_queue = in_queue
        self.main_loop = main_loop
        self.qr_callback = qr_callback
        
        self.last_qr = None
        self.is_connected = False
        self.is_connecting = False
        
        if not master_phone:
            raise ValueError("master_phone is required for WhatsAppHandler")
            
        self.master_phone = str(master_phone).replace("+", "").replace(" ", "").replace("-", "")
        self.master_jid = build_jid(self.master_phone)
        
        data_dir = os.path.join(os.path.dirname(__file__), "data", f"user_{user_id}")
        os.makedirs(data_dir, exist_ok=True)
        session_file = os.path.join(data_dir, "wa_session.sqlite3")
        
        self.client = NewClient(session_file)
        self.processed_ids = set()
        
        @self.client.event(ConnectedEv)
        def on_connected(_: NewClient, __: ConnectedEv):
            print(f"\n[WhatsApp User {self.user_id}] ⚡ Connected to WhatsApp!")
            self.is_connected = True
            self.is_connecting = False
            self.last_qr = None
            self.client.send_presence(Presence.UNAVAILABLE)
            
            # Notify frontend that we are connected
            if self.qr_callback:
                asyncio.run_coroutine_threadsafe(self.qr_callback("CONNECTED"), self.main_loop)

        @self.client.event(QREv)
        def on_qr(_: NewClient, qr: QREv):
            print(f"\n[WhatsApp User {self.user_id}] 📱 QR Code Received!")
            qr_str = qr.QR if hasattr(qr, 'QR') else str(qr)
            if isinstance(qr_str, bytes):
                qr_str = qr_str.decode('utf-8', errors='ignore')
            self.last_qr = qr_str
            if self.qr_callback:
                asyncio.run_coroutine_threadsafe(self.qr_callback(qr_str), self.main_loop)

        @self.client.event(MessageEv)
        def on_message(client: NewClient, message: MessageEv):
            text = ""
            if message.Message.conversation:
                text = message.Message.conversation
            elif message.Message.extendedTextMessage and message.Message.extendedTextMessage.text:
                text = message.Message.extendedTextMessage.text
            
            msg_id = message.Info.ID
            if msg_id in self.processed_ids:
                return
            self.processed_ids.add(msg_id)
            if len(self.processed_ids) > 1000:
                self.processed_ids.clear()
            
            sender = message.Info.MessageSource.Sender
            chat = message.Info.MessageSource.Chat
            sender_alt = message.Info.MessageSource.SenderAlt
            
            combined_ids = str(sender) + str(chat) + str(sender_alt)
            
            if str(self.master_phone) not in combined_ids:
                return
                
            asyncio.run_coroutine_threadsafe(self.in_queue.put((self.user_id, text, message)), self.main_loop)

    def connect(self):
        if self.is_connecting or self.is_connected:
            print(f"\n[WhatsApp User {self.user_id}] Already connected or connecting.")
            return
            
        self.is_connecting = True
        print(f"\n[WhatsApp User {self.user_id}] Starting connection...")
        try:
            self.client.connect()
        except Exception as e:
            print(f"[WhatsApp User {self.user_id}] Connection error: {e}")
        finally:
            self.is_connecting = False
            self.is_connected = False

    def send_to_master(self, text: str):
        if not self.is_connected:
            return
        try:
            self.client.send_message(self.master_jid, text)
        except Exception as e:
            print(f"\n[WhatsApp User {self.user_id}] Failed to send message: {e}")

    def send_sticker_to_master(self, filename: str):
        if not self.is_connected:
            return
        sticker_path = os.path.join(STICKER_DIR, filename)
        if not os.path.exists(sticker_path):
            print(f"[WhatsApp User {self.user_id}] Sticker not found: {sticker_path}")
            return
        try:
            self.client.send_sticker(self.master_jid, sticker_path)
            print(f"[WhatsApp User {self.user_id}] Sticker sent: {filename}")
        except Exception as e:
            print(f"[WhatsApp User {self.user_id}] Failed to send sticker '{filename}': {e}")

    def send_natural_burst(self, text: str):
        if not self.is_connected:
            return
            
        def burst_worker():
            import re
            import time
            import random
            
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]
            
            for i, sentence in enumerate(sentences):
                if i > 0:
                    self.set_typing(True)
                    delay = min(len(sentence) * 0.04, 2.5) 
                    time.sleep(delay + random.uniform(0.1, 0.4))
                    self.set_typing(False)
                    
                self.send_to_master(sentence)
                
                if i < len(sentences) - 1:
                    time.sleep(random.uniform(0.3, 0.7))
                    
        threading.Thread(target=burst_worker, daemon=True).start()

    def mark_read(self, message):
        if not self.is_connected:
            return
        try:
            self.client.mark_read(
                message.Info.ID, 
                chat=message.Info.MessageSource.Chat, 
                sender=message.Info.MessageSource.Sender, 
                receipt=ReceiptType.READ
            )
        except Exception as e:
            print(f"[WhatsApp User {self.user_id}] Failed to send read receipt: {e}")

    def set_typing(self, is_typing: bool):
        if not self.is_connected:
            return
        try:
            presence = ChatPresence.CHAT_PRESENCE_COMPOSING if is_typing else ChatPresence.CHAT_PRESENCE_PAUSED
            self.client.send_chat_presence(self.master_jid, presence, ChatPresenceMedia.CHAT_PRESENCE_MEDIA_TEXT)
        except Exception as e:
            print(f"[WhatsApp User {self.user_id}] Failed to set typing presence: {e}")

    def set_presence(self, available: bool):
        if not self.is_connected:
            return
        try:
            p = Presence.AVAILABLE if available else Presence.UNAVAILABLE
            self.client.send_presence(p)
            status = "🟢 Online" if available else "⚫ Offline"
            print(f"[WhatsApp User {self.user_id}] Presence → {status}")
        except Exception as e:
            print(f"[WhatsApp User {self.user_id}] Failed to set presence: {e}")
