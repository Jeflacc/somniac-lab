from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import time

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)
    is_pro = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_expiry = Column(Float, nullable=True)
    profile_picture = Column(String, nullable=True)  # base64 data URL
    inventory = Column(JSON, default=[])
    timezone = Column(String, default="Asia/Jakarta")
    
    ai_agents = relationship("AIAgent", back_populates="owner")

class AIAgent(Base):
    __tablename__ = "ai_agents"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String, default="Evelyn")
    base_persona = Column(String, default="Helpful and friendly AI assistant.")
    is_sleeping = Column(Boolean, default=False)
    mood = Column(String, default="netral")
    relationship_status = Column(String, default="baru kenal")
    
    hunger = Column(Float, default=0.0)
    sleepiness = Column(Float, default=0.0)
    libido = Column(Float, default=0.0)
    heart_rate = Column(Integer, default=72)
    breath_rate = Column(Integer, default=15)
    last_updated = Column(Float, default=0.0)
    
    # Store complex dynamic state (inventory, memories, multipliers)
    state_data = Column(JSON, default={})
    
    # WhatsApp Multi-Tenant Fields
    whatsapp_number = Column(String, default="")
    whatsapp_connected = Column(Boolean, default=False)
    profile_picture = Column(String, nullable=True)  # base64 data URL
    banner_picture = Column(String, nullable=True)   # base64 data URL
    
    owner = relationship("User", back_populates="ai_agents")
    economy = relationship("Economy", back_populates="agent", uselist=False)
    house_state = relationship("HouseState", back_populates="agent", uselist=False)
    journal_entries = relationship("JournalEntry", back_populates="agent")
    chat_sessions = relationship("ChatSession", back_populates="agent")

class Economy(Base):
    __tablename__ = "economy"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    
    balance = Column(Float, default=50000.0)
    transaction_history = Column(JSON, default=[])
    
    agent = relationship("AIAgent", back_populates="economy")

class HouseState(Base):
    __tablename__ = "house_state"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    
    current_chore_id = Column(String, nullable=True)
    current_chore_start_time = Column(Float, nullable=True)
    
    rooms_data = Column(JSON, default={})
    chore_queue = Column(JSON, default=[])
    
    agent = relationship("AIAgent", back_populates="house_state")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    
    date_str = Column(String, index=True)
    entries = Column(JSON, default=[])
    
    agent = relationship("AIAgent", back_populates="journal_entries")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    
    created_at = Column(Float, default=time.time)
    messages = Column(JSON, default=[])
    
    agent = relationship("AIAgent", back_populates="chat_sessions")
