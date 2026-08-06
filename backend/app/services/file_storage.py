import os
import shutil
from abc import ABC, abstractmethod
from fastapi import UploadFile
from typing import Optional
from app.core.config import settings


class FileStorageService(ABC):
    """
    Abstract Base Class for file storage operations.
    Allows backend to transition between local storage and AWS S3 seamlessly.
    """
    @abstractmethod
    async def save_file(self, file: UploadFile, subfolder: Optional[str] = None) -> str:
        """Saves a file and returns its location path/URL."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes a file from storage."""
        pass


class LocalFileStorage(FileStorageService):
    """
    Local filesystem storage implementation.
    """
    def __init__(self, upload_dir: str = settings.UPLOAD_DIR):
        self.upload_dir = upload_dir
        os.makedirs(self.upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, subfolder: Optional[str] = None) -> str:
        dest_dir = self.upload_dir
        if subfolder:
            dest_dir = os.path.join(dest_dir, subfolder)
            os.makedirs(dest_dir, exist_ok=True)
            
        file_path = os.path.join(dest_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    async def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False


class S3FileStorage(FileStorageService):
    """
    AWS S3 storage implementation placeholder.
    To be fully developed when transitioning production settings to AWS.
    """
    def __init__(self):
        # S3 client instantiation placeholder
        pass

    async def save_file(self, file: UploadFile, subfolder: Optional[str] = None) -> str:
        # Upload to bucket logic
        return f"s3://{settings.AWS_BUCKET_NAME}/{subfolder}/{file.filename}"

    async def delete_file(self, file_path: str) -> bool:
        # Delete from bucket logic
        return True


def get_file_storage() -> FileStorageService:
    """Factory helper to fetch configured storage provider dependency."""
    if settings.STORAGE_PROVIDER.lower() == "s3":
        return S3FileStorage()
    return LocalFileStorage()
