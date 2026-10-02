from fastapi import APIRouter, UploadFile, File
from app.services.file_storage import save_upload_image

router = APIRouter(prefix="/uploads", tags=["uploads"])

    
@router.post("/save")
def save_file(file: UploadFile = File(...)):
    saved = save_upload_image(file)
        
    return {
        "filename": saved["filename"],
        "content_type": saved["content_type"],
        "saved_path": saved["url"]
    }