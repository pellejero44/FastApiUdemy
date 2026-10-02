from fastapi import APIRouter, Depends, HTTPException, status
from .schemas import TokenResponse, OAuth2TokenResponse, UserCreate, UserLogin, UserPublic, RoleUpdate
from fastapi import Path
from app.models.user import User
from app.api.v1.auth.repository import UserRepository
from app.core.db import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.core.security import create_access_token, get_current_user, password_hash, require_admin, oauth2_token


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    existing_user = user_repo.get_by_email(payload.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = password_hash.hash(payload.password)
    new_user = user_repo.create(email=payload.email, hashed_password=hashed_password, fullname=payload.fullname)
    db.commit()
    db.refresh(new_user)
    
    return UserPublic.model_validate(new_user)

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    repository = UserRepository(db)
    user = repository.get_by_email(payload.email)
    if not user or not password_hash.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = create_access_token(sub=user.email)
    return TokenResponse(access_token=access_token, token_type="bearer", user=UserPublic.model_validate(user))

@router.get("/me", response_model=UserPublic)
async def read_me(current: User = Depends(get_current_user)):
    return UserPublic.model_validate(current)

@router.put("/role/{user_id}", response_model=UserPublic)
def set_role(
    user_id: int = Path(..., ge = 1, description="The ID of the user"), 
    payload: RoleUpdate = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin)
    ):
    
    repository = UserRepository(db)
    user = repository.get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    updated_user = repository.set_role(user, payload.role)
    return UserPublic.model_validate(updated_user)

@router.post("/token", response_model=OAuth2TokenResponse)
async def token_endpoint(response = Depends(oauth2_token)):
    return response