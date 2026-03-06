import httpx
import logging
from typing import Optional
from app.core.config import settings
from app.utils import constants

logger = logging.getLogger(__name__)

class StorageClient:
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        raw_url = settings.STORAGE_URL or ""
        self.base_url = raw_url.split("/storage/v1")[0].rstrip("/")
        self.key = settings.STORAGE_KEY
        self.bucket = settings.STORAGE_BUCKET

    async def upload_file(self, file_content: bytes, file_path: str, content_type: str, upsert: bool = False) -> Optional[str]:
        """
        Uploads a file to Supabase Storage and returns a Public URL.
        Assumes the bucket is set to 'Public' in the Supabase Dashboard.
        Uses constants for configuration and timeouts.
        """
        if self.storage_type != constants.STORAGE_TYPE_SUPABASE:
            logger.error(f"Unsupported STORAGE_TYPE: {self.storage_type}")
            return None

        if not self.base_url or not self.key or not self.bucket:
            logger.error("Storage configuration missing.")
            return None

        upload_url = f"{self.base_url}/storage/v1/object/{self.bucket}/{file_path}"
        
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": content_type,
            "x-upsert": "true" if upsert else "false"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    upload_url, 
                    content=file_content, 
                    headers=headers, 
                    timeout=constants.STORAGE_UPLOAD_TIMEOUT
                )
                
                if response.status_code == 200:
                    return f"{self.base_url}/storage/v1/object/public/{self.bucket}/{file_path}"
                else:
                    logger.error(f"Supabase upload failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")

        return None

storage_client = StorageClient()
