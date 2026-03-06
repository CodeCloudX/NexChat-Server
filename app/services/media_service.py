import io
import time
import magic
from PIL import Image
from typing import Tuple, Optional
from fastapi import UploadFile
from app.infrastructure.storage import storage_client
from app.core.exceptions import InvalidFileException, StorageException
from app.utils import constants, helpers

def get_mime_type(buffer: bytes) -> str:
    """Detects actual MIME type from file content."""
    mime = magic.Magic(mime=True)
    return mime.from_buffer(buffer)

def compress_image(image_content: bytes, mime_type: str, max_width: int = 1024, quality: int = 80) -> Tuple[bytes, int, int]:
    """Resizes and compresses images. Returns (content, width, height)."""
    img = Image.open(io.BytesIO(image_content))
    
    if mime_type in ["image/gif", "image/webp"]:
        return image_content, img.width, img.height

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    if img.width > max_width:
        ratio = max_width / float(img.width)
        height = int(float(img.height) * float(ratio))
        img = img.resize((max_width, height), Image.Resampling.LANCZOS)
    
    output = io.BytesIO()
    img.save(output, format="JPEG", optimize=True, quality=quality)
    return output.getvalue(), img.width, img.height

async def upload_profile_photo(user_id: str, file: UploadFile) -> str:
    """Processes and uploads a profile photo."""
    content = await file.read()
    actual_mime = get_mime_type(content)
    
    if not actual_mime.startswith("image/"):
        raise InvalidFileException(detail=f"Profile photo must be an image. Detected: {actual_mime}")

    try:
        # For profile photo, we don't need to return dimensions to DB, 
        # but we use the helper properly.
        compressed, _, _ = compress_image(
            content, "image/jpeg", 
            max_width=constants.PROFILE_PHOTO_MAX_WIDTH, 
            quality=constants.PROFILE_IMAGE_QUALITY
        )
    except Exception:
        compressed = content

    file_path = f"{user_id}/profile/profile_current.jpg"
    base_url = await storage_client.upload_file(
        file_content=compressed, 
        file_path=file_path, 
        content_type="image/jpeg", 
        upsert=True
    )
    
    if not base_url:
        raise StorageException(detail="Could not save profile photo to storage.")
        
    return f"{base_url}?t={int(time.time())}"

async def upload_chat_media(user_id: str, file: UploadFile) -> Tuple[str, str, int, int, int]:
    """Processes and uploads chat media. Returns (url, mime, size, width, height)."""
    content = await file.read()
    actual_mime = get_mime_type(content)
    
    if not actual_mime.startswith("image/"):
        raise InvalidFileException(detail="Only images are allowed in chat.")

    content_to_upload = content
    mime_to_upload = actual_mime
    file_ext = helpers.get_filename_extension(file.filename) or "jpg"
    width, height = 0, 0

    try:
        content_to_upload, width, height = compress_image(
            content, actual_mime, 
            max_width=constants.CHAT_MEDIA_MAX_WIDTH, 
            quality=constants.IMAGE_QUALITY
        )
        if actual_mime not in ["image/gif", "image/webp"]:
            mime_to_upload = "image/jpeg"
            file_ext = "jpg"
    except Exception:
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.width, img.height
        except Exception:
            pass

    file_path = f"{user_id}/media/media_{helpers.generate_uuid()}.{file_ext}"
    url = await storage_client.upload_file(content_to_upload, file_path, mime_to_upload)
    
    if not url:
        raise StorageException(detail="Could not save chat media to storage.")
        
    return url, mime_to_upload, len(content_to_upload), width, height
