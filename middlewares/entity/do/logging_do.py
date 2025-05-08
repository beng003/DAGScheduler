from config.database import Base
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    Enum,
    Index,
    CHAR,
    text,
    JSON,
    Integer,
    Float,
)
from sqlalchemy.dialects.mysql import FLOAT

# ... existing code ...
from datetime import datetime


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    client_host = Column(String(50))
    method = Column(String(10))
    path = Column(String(500))
    status_code = Column(Integer)
    process_time = Column(Float)
    user_agent = Column(String(500))
