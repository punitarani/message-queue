"""db.py"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from mq.config import get_db_url

DATABASE_URL = get_db_url()

# Create Async Engine with Connection Pool Configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,  # Maximum number of permanent connections
    max_overflow=10,  # Maximum number of temporary connections
    pool_timeout=60,  # Maximum wait time for a connection
    pool_recycle=3600,  # Recycle connections after this many seconds
)

# Create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
