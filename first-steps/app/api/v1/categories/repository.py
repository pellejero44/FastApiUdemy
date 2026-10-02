from __future__ import annotations

from typing import Iterable, Sequence
from collections.abc import Iterable as IterableABC

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import CategoryORM


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db



    def list_many(self, *, skip: int = 0, limit: int = 50) -> Sequence[CategoryORM]:
        return self.db.execute(select(CategoryORM).offset(skip).limit(limit)).scalars().all()

    def list_with_total(self, *, page: int = 1, per_page: int = 50) -> tuple[int, list[CategoryORM]]:
        pass

    def get(self, category_id: int) -> CategoryORM | None:
        return self.db.get(CategoryORM, category_id)

    def get_by_slug(self, slug: str) -> CategoryORM | None:
        return self.db.execute(select(CategoryORM).where(CategoryORM.slug == slug)).scalars().first()

    def create(self, *, name: str, slug: str) -> CategoryORM:
       category = CategoryORM(name=name, slug=slug)
       self.db.add(category)
       self.db.flush()
       return category

    def update(self, category: CategoryORM, updates: dict) -> CategoryORM:
        for key, value in updates.items():
            setattr(category, key, value)
            
        self.db.add(category)
        self.db.flush()
        return category

    def delete(self, category: CategoryORM) -> None:
        self.db.delete(category)
        self.db.flush()