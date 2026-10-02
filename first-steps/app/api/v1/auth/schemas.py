
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from app.models.user import Role

class UserBase(BaseModel):
    email: EmailStr
    fullname: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
class UserPublic(UserBase):
    id: int
    role: Role
    is_active: bool
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)
    fullname: Optional[str] = None
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    
class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    sub: str
    username: str

class RoleUpdate(BaseModel):
    role: Role
    
