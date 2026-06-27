import os
import uuid
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Text, Float, Boolean, Integer
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# Get database URL from environment, defaulting to local sqlite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rupeeradar.db")

# SQLite needs specific connect arguments for multithreading
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DBSession(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    status = relationship("DBSessionStatus", back_populates="session", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("DBTransaction", back_populates="session", cascade="all, delete-orphan")
    rules = relationship("DBSessionRule", back_populates="session", cascade="all, delete-orphan")

class DBSessionStatus(Base):
    __tablename__ = "session_statuses"
    
    id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), primary_key=True)
    status = Column(String, default="pending")  # pending | processing | complete | error
    error_message = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    session = relationship("DBSession", back_populates="status")

class DBTransaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False)  # ISO YYYY-MM-DD
    raw_description = Column(Text, nullable=False)
    clean_description = Column(Text, nullable=False)
    merchant = Column(String, nullable=True)
    amount = Column(Float, nullable=False)  # negative = expense, positive = income
    type = Column(String, nullable=False)  # debit | credit
    category = Column(String, default="Other")
    category_confidence = Column(Float, default=1.0)
    category_source = Column(String, default="rule")
    is_recurring = Column(Boolean, default=False)
    recurring_group_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)

    session = relationship("DBSession", back_populates="transactions")

class DBSessionRule(Base):
    __tablename__ = "session_rules"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    pattern = Column(String, nullable=False)  # e.g., merchant name to match
    category = Column(String, nullable=False)

    session = relationship("DBSession", back_populates="rules")

class DBLLMLog(Base):
    __tablename__ = "llm_logs"
    
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    model = Column(String, index=True, nullable=False)
    tokens_used = Column(Integer, nullable=False)

def init_db():

    # Make sure parent directory exists if using SQLite relative/absolute path
    if DATABASE_URL.startswith("sqlite:///"):
        db_path = DATABASE_URL.replace("sqlite:///", "")
        # Remove any query params
        db_path = db_path.split("?")[0]
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
    Base.metadata.create_all(bind=engine)

def get_db_context():
    """Context manager for DB sessions."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Session Helper Functions
def create_session(db: Session, expires_in_hours: int = 24) -> DBSession:
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    db_session = DBSession(id=session_id, expires_at=expires_at)
    db_status = DBSessionStatus(id=session_id, status="pending")
    
    db.add(db_session)
    db.add(db_status)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session(db: Session, session_id: str) -> Optional[DBSession]:
    """Fetch a session only if it exists AND has not expired (TTL check — ING-45)."""
    now = datetime.utcnow()
    return (
        db.query(DBSession)
        .filter(DBSession.id == session_id, DBSession.expires_at >= now)
        .first()
    )

def update_session_status(db: Session, session_id: str, status: str, error_message: Optional[str] = None) -> Optional[DBSessionStatus]:
    db_status = db.query(DBSessionStatus).filter(DBSessionStatus.id == session_id).first()
    if db_status:
        db_status.status = status
        db_status.error_message = error_message
        db_status.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_status)
    return db_status

def delete_session(db: Session, session_id: str) -> bool:
    db_session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if db_session:
        db.delete(db_session)
        db.commit()
        return True
    return False

def clean_expired_sessions(db: Session) -> int:
    import shutil
    
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    
    now = datetime.utcnow()
    expired = db.query(DBSession).filter(DBSession.expires_at < now).all()
    count = len(expired)
    for session in expired:
        # Physically delete uploads folder
        session_upload_dir = os.path.join(upload_dir, session.id)
        if os.path.exists(session_upload_dir):
            try:
                shutil.rmtree(session_upload_dir)
            except Exception as e:
                print(f"Warning: Failed to delete expired session upload dir {session_upload_dir}: {str(e)}")
                
        db.delete(session)
    if count > 0:
        db.commit()
    return count
