import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# It's good practice to get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kairos:kairos_secret@localhost:5432/kairos_dev")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Dependency to get a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()