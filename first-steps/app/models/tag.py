from __future__ import annotations
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, Integer
from typing import List, TYPE_CHECKING
from app.core.db import Base

if TYPE_CHECKING:
    from .post import PostORM

class TagORM(Base):
    __tablename__ = "tags"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    
    posts: Mapped[List["PostORM"]] = relationship(
        secondary="post_tags", 
        back_populates="tags",
        lazy="selectin",
        passive_deletes=True
    )