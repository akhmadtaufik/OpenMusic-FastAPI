"""Storage service for MinIO object storage operations.

Uses the native minio Python library. All blocking I/O operations are wrapped
with run_in_threadpool to avoid blocking the FastAPI async event loop.
"""

from io import BytesIO
from fastapi import UploadFile, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from minio import Minio
from minio.error import S3Error
from app.core.config import settings


class StorageService:
    """Service for handling file uploads to MinIO object storage.

    Attributes:
        client: MinIO client instance.
        bucket: Target bucket name for uploads.
    """

    def __init__(self):
        """Initialize MinIO client with configuration from settings."""
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False  # Local dev without SSL
        )
        self.bucket = settings.MINIO_BUCKET_NAME

    async def upload_file(self, file: UploadFile, filename: str) -> str:
        """Upload a file to MinIO storage.

        Args:
            file: The uploaded file from the request.
            filename: Target filename in the bucket.

        Returns:
            str: Public URL of the uploaded file.

        Raises:
            HTTPException: If upload fails.
        """
        try:
            content = await file.read()
            content_stream = BytesIO(content)
            content_type = file.content_type or "application/octet-stream"

            # Wrap sync minio call in threadpool to avoid blocking
            await run_in_threadpool(
                self.client.put_object,
                self.bucket,
                filename,
                content_stream,
                length=len(content),
                content_type=content_type
            )

            # Construct public URL
            return f"http://{settings.MINIO_ENDPOINT}/{self.bucket}/{filename}"

        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )


# Singleton instance for dependency injection
storage_service = StorageService()
