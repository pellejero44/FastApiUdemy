import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile, File, status


MEDIA_DIR = os.path.join(os.path.dirname(__file__), "..", "media")
MEDIA_DIR = os.path.normpath(MEDIA_DIR)
ALLOWED_MIME = {"image/jpeg", "image/png"}
MAX_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "4"))  
CHUNKS = 1024 * 1024  # 1 MB

def ensure_media_dir_exists() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)

def save_upload_image(file: UploadFile = File(...)) -> dict:
    if(file.content_type not in ALLOWED_MIME):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type. Only JPEG and PNG are allowed.")
    
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    ensure_media_dir_exists()
    file_path = os.path.join(MEDIA_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer, length=CHUNKS)
        
    size_mb = os.path.getsize(file_path)
    if size_mb > MAX_MB * CHUNKS:
        os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the maximum limit of {MAX_MB} MB.")
    
    return {
        "filename": filename,
        "content_type": file.content_type,
        "saved_path": file_path
    }