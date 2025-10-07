from sqlalchemy.orm import Session
from . import models, schemas
from passlib.context import CryptContext

# It's good practice to create a single CryptContext instance for the application
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- User CRUD ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Value CRUD ---

def get_value(db: Session, value_id: int):
    """Gets a single value by its ID."""
    return db.query(models.Value).filter(models.Value.id == value_id).first()

def get_values_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Value).filter(models.Value.owner_id == user_id).offset(skip).limit(limit).all()

def create_user_value(db: Session, value: schemas.ValueCreate, user_id: int):
    db_value = models.Value(**value.dict(), owner_id=user_id)
    db.add(db_value)
    db.commit()
    db.refresh(db_value)
    return db_value

def update_value(db: Session, db_value: models.Value, value_in: schemas.ValueCreate):
    """Updates a value in the database."""
    # Pydantic v2 uses model_dump, but we stick to dict for broader compatibility
    value_data = value_in.dict(exclude_unset=True)
    for key, value in value_data.items():
        setattr(db_value, key, value)
    db.add(db_value)
    db.commit()
    db.refresh(db_value)
    return db_value

def delete_value(db: Session, db_value: models.Value):
    """Deletes a value from the database."""
    db.delete(db_value)
    db.commit()
    return db_value