from app.core.db import Base, engine, SessionLocal
from fastapi import FastAPI
from dotenv import load_dotenv
from app.api.v1.post.router import router as post_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as uploads_router
from app.api.v1.tags.router import router as tags_router
from app.api.v1.categories.router import router as categories_router
from fastapi.staticfiles import StaticFiles
from app.models.user import User
from app.core.security import password_hash
from app.core.middleware import register_middleware
import os

load_dotenv()

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
MEDIA_DIR = os.path.normpath(MEDIA_DIR)

def seed_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "angel@example.com").first()
        if not existing:
            admin = User(
                email="angel@example.com",
                hashed_password=password_hash.hash("123abc"),
                fullname="Angel Gomes",
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title="Mini blog", swagger_ui_parameters={"persistAuthorization": True})
    Base.metadata.create_all(bind=engine) # dev
    register_middleware(app)
    seed_admin()
    app.include_router(post_router)
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(uploads_router, prefix="/api/v1")
    app.include_router(tags_router, prefix="/api/v1")
    app.include_router(categories_router, prefix="/api/v1")
    
    os.makedirs(MEDIA_DIR, exist_ok=True)
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

    return app

app = create_app()







