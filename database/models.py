from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import datetime

Base = declarative_base()

class AuctionSession(Base):
    __tablename__ = "auction_sessions"
    
    id = Column(Integer, primary_key=True)
    session_name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to snapshots
    snapshots = relationship("StateSnapshot", back_populates="session", cascade="all, delete-orphan")

class StateSnapshot(Base):
    __tablename__ = "state_snapshots"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("auction_sessions.id"), nullable=False)
    state_json = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship to session
    session = relationship("AuctionSession", back_populates="snapshots")
