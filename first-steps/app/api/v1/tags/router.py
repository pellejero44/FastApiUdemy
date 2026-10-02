from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1.tags.repository import TagRepository
from app.core.db import get_db 
from app.core.security import require_editor, require_admin, require_user
from app.api.v1.tags.schemas import TagCreate, TagPublic, TagUpdate
from app.models.user import User


router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("", response_model=dict, response_description="Lista de tags", status_code=status.HTTP_200_OK)
def list_tags(
   page: int = Query(1, ge=1),
   per_page: int = Query(10, ge=1, le=100),
   order_by: str = Query("id", regex="^(id|name)$"),
   direction: str = Query("asc", regex="^(asc|desc)$"),
   search: str | None = Query(None, min_length=1, max_length=50),
    db: Session = Depends(get_db),
):
    tag_repo = TagRepository(db)
    return tag_repo.list_tags(search= search, order_by=order_by, direction=direction, page=page, per_page=per_page)


@router.post("", response_model=TagPublic, response_description="Tag creado correctamente", status_code=status.HTTP_201_CREATED)
def create_tag(tag: TagCreate, db: Session = Depends(get_db), _editor: User = Depends(require_editor)):
    tag_repo = TagRepository(db)
    try:
        tag_obj = tag_repo.create_tag(tag.name)
        db.commit()
        db.refresh(tag_obj)
        return tag_obj
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.put("/{tag_id}", response_model=TagPublic, response_description="Tag actualizado correctamente", status_code=status.HTTP_200_OK)
def update_tag(tag_id: int, tag: TagUpdate, db: Session = Depends(get_db), _editor: User = Depends(require_editor)):
    tag_repo = TagRepository(db)
    try:
        tag_obj = tag_repo.update(tag_id, tag.name)
        if not tag_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        
        db.commit()
        db.refresh(tag_obj)
        return TagPublic.model_validate(tag_obj)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{tag_id}", response_description="Tag eliminado correctamente", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db), _editor: User = Depends(require_admin)):
    tag_repo = TagRepository(db)
    try:
        tag_obj = tag_repo.delete(tag_id)
        if not tag_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
        
        db.commit()
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
@router.get("/popular/top")
def get_most_popular_tags(db: Session = Depends(get_db), _editor: User = Depends(require_user)):
    tag_repo = TagRepository(db)
    row = tag_repo.most_popular()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No popular tags found")
    
    return row