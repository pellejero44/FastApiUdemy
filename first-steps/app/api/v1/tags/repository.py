from typing import List, Optional, Tuple
from app.services.pagination import paginate_query
from app.api.v1.tags.schemas import TagPublic
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from app.models.post import PostORM, post_tags
from app.models.tag import TagORM

class TagRepository:
    
    def __init__(self, db: Session):
        self.db = db
        
    def get(self, tag_id: int) -> Optional[TagORM]:
        return self.db.execute(select(TagORM).where(TagORM.id == tag_id)).scalar_one_or_none()
    
    def list_tags(
        self,
        search: Optional[str],
        order_by: str,
        direction: str,
        page: int,
        per_page: int
        ) -> Tuple[int, List[TagORM]]:
        
        query = select(TagORM)
        if search:
            query = query.where(func.lower(TagORM.name).like(f"%{search.lower()}%"))
            
        allowed_order = {
            "id": TagORM.id,
            "name": func.lower(TagORM.name)
        }
        
        result = paginate_query(
            db=self.db,
            model=TagORM,
            base_query=query,
            page=page,
            per_page=per_page,
            order_by=order_by,
            direction=direction,
            allowed_order_by=allowed_order
        )
        
        result["items"] = [TagPublic.model_validate(item) for item in result["items"]]
        
        return result
        
        
    def create_tag(self, name: str):
        normalized_name = name.strip().lower()
        tag_obj = self.db.execute(select(TagORM).where(func.lower(TagORM.name) == normalized_name)).scalar_one_or_none()
        
        if tag_obj:
            return tag_obj
        
        tag_obj = TagORM(name=name)
        self.db.add(tag_obj)
        self.db.flush() 
        return tag_obj
    
    def update(self, tag_id: int, name: str) -> Optional[TagORM]:
        tag_obj = self.get(tag_id)
        
        if not tag_obj:
            return None
        
        if name is not None:
            tag_obj.name = name
        
        self.db.add(tag_obj)
        self.db.flush()
        self.db.refresh(tag_obj)
        
        return tag_obj
    
    def delete(self, tag_id: int) -> bool:
        tag_obj = self.get(tag_id)
        
        if not tag_obj:
            return False
        
        self.db.delete(tag_obj)
        self.db.flush()
        return True
    
    def most_popular(self) -> List[TagORM]:
        row = (
            self.db.execute(
                select(
                    TagORM.id.label("id"),
                    TagORM.name.label("name"),
                    func.count(PostORM.id).label("uses")
                )
                .join(post_tags, post_tags.c.tag_id == TagORM.id)
                .join(PostORM, PostORM.id == post_tags.c.post_id)
                .group_by(TagORM.id)
                .order_by(func.count(PostORM.id).desc(), func.lower(TagORM.name).asc())
                .limit(1)
            )
            .mappings()
            .first()
        )
     
        return dict(row) if row else None