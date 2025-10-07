from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas, security
from .db.database import SessionLocal, engine, get_db

app = FastAPI(
    title="Kairos API",
    description="Backend for the Kairos application, helping users navigate their pivotal moments.",
    version="0.1.0",
)

# --- Authentication Dependencies ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token, credentials_exception)
    email: str = payload.get("sub")
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- API Endpoints ---

@app.get("/")
async def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Welcome to the Kairos API. Your journey begins now."}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        data={"sub": user.email}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

# --- Value Compass Endpoints ---

@app.post("/users/me/values/", response_model=schemas.Value, status_code=status.HTTP_201_CREATED)
def create_value_for_current_user(
    value: schemas.ValueCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new value for the currently authenticated user.
    """
    return crud.create_user_value(db=db, value=value, user_id=current_user.id)

@app.get("/users/me/values/", response_model=List[schemas.Value])
def read_values_for_current_user(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve all values for the currently authenticated user.
    """
    return crud.get_values_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)

@app.put("/users/me/values/{value_id}", response_model=schemas.Value)
def update_value_for_current_user(
    value_id: int,
    value_in: schemas.ValueCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a specific value for the currently authenticated user.
    """
    db_value = crud.get_value(db, value_id=value_id)
    if db_value is None:
        raise HTTPException(status_code=404, detail="Value not found")
    if db_value.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this value")
    return crud.update_value(db=db, db_value=db_value, value_in=value_in)

@app.delete("/users/me/values/{value_id}", response_model=schemas.Value)
def delete_value_for_current_user(
    value_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a specific value for the currently authenticated user.
    """
    db_value = crud.get_value(db, value_id=value_id)
    if db_value is None:
        raise HTTPException(status_code=404, detail="Value not found")
    if db_value.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this value")
    return crud.delete_value(db=db, db_value=db_value)