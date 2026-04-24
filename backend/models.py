from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    ai_instances = relationship("AIInstance", back_populates="owner")
    economy = relationship("Economy", back_populates="owner", uselist=False)
    house_state = relationship("HouseState", back_populates="owner", uselist=False)

class AIInstance(Base):
    __tablename__ = "ai_instances"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String, default="Evelyn")
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
    
    owner = relationship("User", back_populates="ai_instances")

class Economy(Base):
    __tablename__ = "economy"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    balance = Column(Float, default=50000.0)
    transaction_history = Column(JSON, default=[])
    
    owner = relationship("User", back_populates="economy")

class HouseState(Base):
    __tablename__ = "house_state"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    current_chore_id = Column(String, nullable=True)
    current_chore_start_time = Column(Float, nullable=True)
    
    rooms_data = Column(JSON, default={})
    chore_queue = Column(JSON, default=[])
    
    owner = relationship("User", back_populates="house_state")

class JournalEntry(Base):
    __tablename__ = "journal_entries"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    date_str = Column(String, index=True)
    entries = Column(JSON, default=[])
