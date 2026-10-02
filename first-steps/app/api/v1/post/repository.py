from math import ceil
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, select
from app.models import PostORM, User, TagORM
from fastapi import Depends
from app.core.security import get_current_user
from app.utils.slugify_utils import ensure_unique_slug, slugify_base


class PostRepository:
    def __init__(self, db: Session):
        self.db = db
        
    def get(self, post_id: int) -> Optional[PostORM]:
        
        post_find  = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()
    
    def get_by_slug(self, slug: str) -> Optional[PostORM]:
        post_find  = select(PostORM).where(PostORM.slug == slug)
        return self.db.execute(post_find).scalar_one_or_none()
    
    def search(self, query: Optional[str], order_by: str, direction: str, page: int, per_page: int) -> Tuple[int, List[PostORM]]:
        results = select(PostORM)
    
        if query:
             results = results.where(PostORM.title.ilike(f"%{query}%"))
        
    
        total = self.db.scalar(select(func.count()).select_from(results.subquery())) or 0
        
        if total == 0:
            return 0, []

        current_page =  min(page, max(1, ceil(total / per_page) ))
    
        order_col = PostORM.id if order_by == "id" else func.lower(PostORM.title)
        
        result = results.order_by(
            order_col.asc() if direction == "asc" else order_col.desc())
    

        start = (current_page - 1) * per_page        
        items = self.db.execute(result.offset(start).limit(per_page)).scalars().all()
        
        return total, items
    
    def by_tags(self, tags: List[str]) -> List[PostORM]:
        normalized_tags_names = [tag.strip().lower() for tag in tags if tag.strip()]
        if not normalized_tags_names:
            return []
        
        post_list = select(PostORM).options(
            selectinload(PostORM.tags),
            joinedload(PostORM.user),
            ).where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tags_names))).order_by(PostORM.id.asc())
        
        return self.db.execute(post_list).scalars().all()
    
    def ensure_author(self, name: str, email: str) -> User:
 
        author_obj = self.db.execute(
            select(User)
            .where(User.email == email)).scalar_one_or_none()

        return author_obj
    
    def ensure_tags(self, name: str) -> TagORM:
        normalized_name = name.strip().lower()
        tag_obj = self.db.execute(select(TagORM).where(func.lower(TagORM.name) == normalized_name)).scalar_one_or_none()
        
        if tag_obj:
            return tag_obj
        
        tag_obj = TagORM(name=name)
        self.db.add(tag_obj)
        self.db.flush() 
        return tag_obj
    
    def create_post(self, title: str, content: str, tags: List[dict], image_url: str, category_id: Optional[int], author: User = Depends(get_current_user)) -> PostORM:
        author_obj = None
        if author:
            author_obj = self.ensure_author(author.fullname, author.email)
            
        unique_slug = ensure_unique_slug(self.db, title)
        
        post_obj = PostORM(title=title, slug=unique_slug, content=content, 
                           image_url=image_url, user=author_obj, category_id=category_id)
        

        names = tags[0]["name"].split(",")
        for name in names:
            name = name.strip().lower()
            if not name:
                continue
            tag_obj = self.ensure_tags(name)
            post_obj.tags.append(tag_obj)
        
        self.db.add(post_obj)
        self.db.flush()
        self.db.refresh(post_obj)
        
        return post_obj
    
    def update_post(self, post: PostORM, updates: dict) -> PostORM:
        for key, value in updates.items():
            setattr(post, key, value)

        return post
    
    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)
