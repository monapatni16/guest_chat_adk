# db.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("CHAT_DB_URL", "sqlite:///./guest_chat.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()

class GuestSession(Base):
    __tablename__ = "guest_sessions"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("Message", back_populates="guest", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guest_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'agent'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    guest = relationship("GuestSession", back_populates="messages")

def init_db():
    Base.metadata.create_all(bind=engine)
