from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.db import get_db
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.core.config import Settings
from pwdlib import PasswordHash
from app.api.v1.auth.repository import UserRepository



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
password_hash = PasswordHash.recommended()

credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def raise_expired_token():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

def raise_forbidden():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource",
        headers={"WWW-Authenticate": "Bearer"},
    )

def invalid_credentials():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )

# async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     expire = datetime.now(
#         tz=timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
        
#     to_encode.update({"exp": expire})
#     return jwt.encode(payload=to_encode, key=Settings.JWT_SECRET, algorithm=Settings.JWT_ALGORITHM)

def create_access_token(sub: str, minutes: int | None = None):
    expire = datetime.now(
        tz=timezone.utc) + timedelta(minutes=minutes or Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload={"sub": sub, "exp": expire}, key=Settings.JWT_SECRET, algorithm=Settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(jwt=token, key=Settings.JWT_SECRET, algorithms=[Settings.JWT_ALGORITHM])

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_access_token(token)
        sub: Optional[str] = payload.get("sub")
       
        if not sub:
            raise credentials_exception
        
        user_id= int(sub)
    except jwt.ExpiredSignatureError:
        raise raise_expired_token()
    except jwt.InvalidTokenError:
        raise credentials_exception
    except jwt.PyJWTError:
        raise invalid_credentials()
    
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise invalid_credentials()
    
    return user
    
def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

def require_role(required_role: Literal["admin", "user", "editor"]):
    order = {"admin": 2, "editor": 1, "user": 0}
    
    def evaluation(user: User = Depends(get_current_user)) -> User:
        if order[user.role] < order[required_role]:
            raise raise_forbidden()
        return user

    return evaluation

async def oauth2_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    repository = UserRepository(db)
    user = repository.get_by_email(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise invalid_credentials()
    token =  create_access_token(sub=str(user.id))
    return {"access_token": token, "token_type": "bearer"}

require_admin = require_role("admin")
require_editor = require_role("editor")
require_user = require_role("user")