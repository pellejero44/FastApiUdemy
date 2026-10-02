from math import ceil
from typing import Literal, Optional, Union, Annotated
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from app.core.db import get_db
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, UploadFile, File
from .schemas import (PostPublic, PostSummary, PaginatedPosts, PostCreate, PostUpdate)
from .repository import PostRepository
from app.core.security import oauth2_scheme, get_current_user
from app.services.file_storage import save_upload_image

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/", response_model=PaginatedPosts)
def get_posts(
    text: Optional[str] = Query(
    default=None,
    deprecated=True,
    description="Texto a buscar en los títulos de los posts (parámetro obsoleto, usar 'search' en su lugar)",
    ),
    query: Optional[str] = Query(
    default=None,
    description="Texto a buscar en los títulos de los posts",
    alias="search",
    min_length=3,
    max_length=50,
    pattern="^[a-zA-Z0-9 ]+$"
    ),
    per_page: int = Query(
        10,
        ge=1,
        le=50,
        description="Número máximo de posts a devolver (entre 1 y 50)"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Número de página a devolver (debe ser un número entero >= 1)"
    ),
    order_by: Literal["id", "title"] = Query(
        "id",
        description="Campo por el cual ordenar los posts"
    ),
    direction: Literal["asc", "desc"] = Query(
        "asc",
        description="Dirección de ordenamiento de los posts"
    ),
    db: Session = Depends(get_db)
    ):
    
    repository = PostRepository(db)
    query = query or text
    total, items = repository.search(query, order_by, direction, page, per_page)
    
    total_pages = ceil(total / per_page) if total > 0 else 0
    current_page = 1 if total_pages == 0 else min(page, total_pages)
    return PaginatedPosts(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=current_page < total_pages,
        has_prev=current_page > 1,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items
    )
    
@router.get("/by-tags", response_model=list[PostPublic])
def get_posts_by_tags(
    tags: list[str] = Query(
        ...,
        description="Lista de etiquetas para filtrar los posts",
        min_length=1,
        max_length=10),
    db: Session = Depends(get_db)
):
    repository = PostRepository(db)
    return repository.by_tags(tags)


@router.get("/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Devuelve el post completo o solo un resumen según el parámetro 'include_content'")
def get_post(post_id: int = Path(
    ..., 
    ge=1,
    title="ID del post",
    description="El ID del post que deseas obtener (debe ser un número entero mayor o igual a 1)"
    ), 
    include_content: bool | None = Query(default=True, description="Incluir el contenido del post en la respuesta"),
    db: Session = Depends(get_db)
    ):
    
    repository = PostRepository(db)
    post = repository.get(post_id)
    
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)
    
    return PostSummary.model_validate(post, from_attributes=True)


@router.post("",  response_model=PostPublic, response_description="Devuelve el post creado", status_code=status.HTTP_201_CREATED)
def create_post(post: Annotated[PostCreate, Depends(PostCreate.as_form)], image: Optional[UploadFile] = File(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = PostRepository(db)
    saved = None

    try:
        if image is not None:            
            saved = save_upload_image(image)
        
        image_url = saved["saved_path"] if saved else None
        
        post = repository.create_post(
            title=post.title,
            content=post.content,
            category_id=post.category_id,
            tags=[tag.model_dump() for tag in post.tags],
            author= user,
            image_url= image_url
        )
        db.commit()
        db.refresh(post)
        return post
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="El título del post ya existe")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el post")
    
    
@router.put("/{post_id}",  response_model=PostPublic, response_description="Devuelve el post actualizado")
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = PostRepository(db)
    post = repository.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    try:
        updated_post = repository.update_post(post, data.model_dump(exclude_unset=True))
        db.commit()
        db.refresh(updated_post)
        return updated_post
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al actualizar el post")

    
    
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT, response_description="Post eliminado correctamente")
def delete_post(post_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    repository = PostRepository(db)
    post = repository.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")

    try:
        repository.delete_post(post)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al eliminar el post")

@router.get("/slug/{slug}", response_model=Union[PostPublic, PostSummary])
def get_post_by_slug(slug: str, include_content: bool | None = Query(default=True, description="Incluir el contenido del post en la respuesta"),
                     db: Session = Depends(get_db)):
    repository = PostRepository(db)
    post = repository.get_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado")
    
    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)
    
    return PostSummary.model_validate(post, from_attributes=True)
  
@router.get("/secure")
def secure_endpoint(token: str = Depends(oauth2_scheme)):
    return {"message": "Acceso autorizado", "token": token}