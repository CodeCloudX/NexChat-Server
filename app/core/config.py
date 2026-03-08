from typing import Any, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NexChat"
    
    # Environment
    APP_NAME: Optional[str] = "NexChat"
    ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CORE SETTINGS
    SECRET_KEY: str # Still used for hashing or internal signatures if needed
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = []
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]], info: Any) -> Union[List[str], str]:
        if not v and "CORS_ORIGINS" in info.data:
            v = info.data["CORS_ORIGINS"]
            
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return v

    # DATABASE
    DATABASE_URL: str

    # REDIS
    REDIS_URL: str

    # STORAGE
    STORAGE_TYPE: str = "supabase"  # 'supabase' (REST) or 's3' (Boto3)
    STORAGE_URL: Optional[str] = None
    STORAGE_KEY: Optional[str] = None  # Service Role Key for Supabase / Secret Key for S3
    STORAGE_BUCKET: Optional[str] = None
    
    # S3 Specific (Only needed if STORAGE_TYPE=s3)
    S3_ACCESS_KEY: Optional[str] = None

    # PUSH NOTIFICATIONS / GOOGLE AUTH
    FIREBASE_CREDENTIALS: Optional[str] = "firebase/service-account.json"

    # EMAIL SETTINGS (Brevo API only)
    BREVO_API_KEY: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = "NexChat"

    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
