from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Value Schemas ---

class ValueBase(BaseModel):
    title: str
    description: Optional[str] = None

class ValueCreate(ValueBase):
    pass

class Value(ValueBase):
    id: int
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- User Schemas ---

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    values: List[Value] = []

    model_config = ConfigDict(from_attributes=True)

# --- Token Schemas for Authentication ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None