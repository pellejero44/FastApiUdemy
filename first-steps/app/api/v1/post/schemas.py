
from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
from app.api.v1.auth.schemas import UserPublic
from typing import Annotated, Literal, Optional, List
from app.api.v1.categories.schemas import CategoryPublic

class Tag(BaseModel):
    name: str = Field(..., min_length=1, max_length=30, description="El nombre de la etiqueta (entre 1 y 30 caracteres)", example="Python")
    
    model_config = ConfigDict(from_attributes=True)

class Author(BaseModel):
    name: str = Field(..., min_length=3, max_length=10, description="El nombre del autor (entre 3 y 10 caracteres)", example="Pablo")
    email: EmailStr = Field(..., example="pablo@example.com")
    
    model_config = ConfigDict(from_attributes=True)
    
class PostBase(BaseModel):
    title: str
    content: Optional[str] = "no hay contenido"
    tags: Optional[List[Tag]] = Field(default_factory=list)
    user: Optional[UserPublic] = None
    image_url: Optional[str] = None
    category: Optional[CategoryPublic] = None
    
    model_config = ConfigDict(from_attributes=True)

NOT_ALLOWED_WORDS = ["spam", "clickbait", "fake"]

class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="El título del post (entre 3 y 100 caracteres)",
        example="Mi primer post")
    content: Optional[str] = Field(
        default="no hay contenido",
        min_length=10,
        description="El contenido del post",
        example="Este es el contenido de mi primer post")
    category_id: Optional[int] = None
    tags: List[Tag] = []
    
    @field_validator("title")
    @classmethod
    def not_allow_empty_title(cls, value: str) -> str:
        for word in NOT_ALLOWED_WORDS:
            if word in value.lower():
                raise ValueError(f"El título no puede contener la palabra '{word}'")
        return value
    
    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(..., min_length=3)],
        content: Annotated[Optional[str], Form(min_length=10)],
        category_id: Annotated[Optional[int], Form(ge=1)] = None,
        tags: Annotated[Optional[List[str]], Form()] = None,
    ):
        tags_list = [Tag(name=tag) for tag in tags] if tags else []
        return cls(title=title, content=content, category_id=category_id, tags=tags_list)

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = None
    
class PostPublic(PostBase):
    id: int
    slug: str
    model_config = ConfigDict(from_attributes=True)

class PostSummary(BaseModel):
    id: int
    title: str
    
    model_config = ConfigDict(from_attributes=True)

class PaginatedPosts(BaseModel):
    page: int
    per_page: int
    total: int    
    total_pages: int
    has_prev: bool
    has_next: bool    
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: Optional[str] = None
    items: List[PostPublic]