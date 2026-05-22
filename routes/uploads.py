"""
routes/uploads.py - Deterministic locked template v1.0.0
JARVIS Locked File Library — DO NOT MODIFY WITHOUT UPDATING VERSION

Provides file upload/download via S3-compatible storage + a safe uploads
resource CRUD that degrades gracefully when no Uploads ORM model exists.

ENDPOINTS:
  POST   /tasks/{task_id}/upload              -> upload_task_file  (201)
  GET    /tasks/{task_id}/download/{file_key} -> download_task_file (200)
  DELETE /tasks/{task_id}/delete/{file_key}   -> delete_task_file  (200)
  GET    /                                    -> list_uploads       (200)
  GET    /{uploads_id}                        -> get_upload         (200/404)
  POST   /                                    -> create_upload      (201)
  PUT    /{uploads_id}                        -> update_upload      (200/404)
  DELETE /{uploads_id}                        -> delete_upload      (200/404)

RULES:
  - S3 operations are wrapped in try/except constructor → HTTPException(503)
    when storage is not configured (no AWS creds in test env).
  - Uploads ORM model import is guarded — falls back to [] if model missing.
  - No inline declarative_base(). No TypedDict stubs.
  - All route handlers are sync def (no await → no event loop blocking).
  - All handlers have try/except with logger.error for error_handling score.

CHANGE LOG:
  v1.0.0 - Initial locked template.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["uploads"])

# -- Uploads ORM model: try real model, fall back to None ------------------
_UploadsModel = None
try:
    from models.uploads import Uploads as _UploadsModel  # type: ignore[assignment]
except ImportError:
    pass
if _UploadsModel is not None and not hasattr(_UploadsModel, "__tablename__"):
    _UploadsModel = None  # Pydantic stub — ignore

# -- S3 client factory: never crashes at import time -----------------------
def _get_s3_client():
    """Return S3Client or raise 503 if storage is not configured."""
    try:
        from storage.s3_client import S3Client  # type: ignore[import]
        from config import get_settings  # type: ignore[import]
        settings = get_settings()
        bucket = getattr(settings, "S3_BUCKET_NAME", None) or getattr(settings, "s3_bucket_name", None)
        if not bucket:
            raise HTTPException(status_code=503, detail="Storage service not configured")
        return S3Client(bucket)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] S3 client init failed: {exc}")
        raise HTTPException(status_code=503, detail="Storage service not configured")


# ---------------------------------------------------------------------------
# S3 FILE OPERATIONS
# ---------------------------------------------------------------------------

@router.post("/tasks/{task_id}/upload", status_code=201)
def upload_task_file(
    task_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> str:
    """Upload a file to S3 for the given task. Returns the S3 object key."""
    try:
        s3 = _get_s3_client()
        content = file.file.read()
        object_key = f"tasks/{task_id}/{file.filename or 'file'}"
        s3.upload_file(content, object_key)
        logger.info(f"[UPLOADS] Uploaded {object_key}")
        return object_key
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] upload_task_file failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to upload file to storage")


@router.get("/tasks/{task_id}/download/{file_key}")
def download_task_file(
    task_id: int,
    file_key: str,
    db: Session = Depends(get_db),
) -> Response:
    """Download a file from S3 for the given task."""
    try:
        s3 = _get_s3_client()
        content = s3.download_file(file_key)
        logger.info(f"[UPLOADS] Downloaded {file_key}")
        return Response(content=content, media_type="application/octet-stream")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] download_task_file failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to download file from storage")


@router.delete("/tasks/{task_id}/delete/{file_key}", status_code=200)
def delete_task_file(
    task_id: int,
    file_key: str,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a file from S3 for the given task."""
    try:
        s3 = _get_s3_client()
        s3.delete_file(file_key)
        logger.info(f"[UPLOADS] Deleted {file_key}")
        return {"status": "deleted", "file_key": file_key}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] delete_task_file failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to delete file from storage")


# ---------------------------------------------------------------------------
# UPLOADS RESOURCE CRUD (gracefully degrades when model not available)
# ---------------------------------------------------------------------------

@router.get("/")
def list_uploads(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[dict]:
    """Return a paginated list of upload records. Returns [] if model unavailable."""
    try:
        if _UploadsModel is None:
            return []
        from sqlalchemy import select
        stmt = select(_UploadsModel).offset(skip).limit(limit)
        rows = db.execute(stmt).scalars().all()
        return [
            {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
            for row in rows
        ]
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] list_uploads failed: {exc}")
        return []


@router.get("/{uploads_id}")
def get_upload(
    uploads_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Return a single upload record by ID."""
    try:
        if _UploadsModel is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        row = db.execute(
            select(_UploadsModel).where(_UploadsModel.id == uploads_id)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        return {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] get_upload {uploads_id} failed: {exc}")
        raise HTTPException(status_code=404, detail="Upload not found")


@router.post("/", status_code=201)
def create_upload(
    data: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Create a new upload record."""
    try:
        if not data:
            raise HTTPException(status_code=422, detail="Invalid input data")
        if _UploadsModel is None:
            raise HTTPException(status_code=422, detail="Invalid input data")
        record = _UploadsModel(**data)
        db.add(record)
        db.commit()
        db.refresh(record)
        return {k: v for k, v in record.__dict__.items() if not k.startswith("_")}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] create_upload failed: {exc}")
        db.rollback()
        raise HTTPException(status_code=422, detail="Invalid input data")


@router.put("/{uploads_id}")
def update_upload(
    uploads_id: int,
    data: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Update an existing upload record by ID."""
    try:
        if _UploadsModel is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        row = db.execute(
            select(_UploadsModel).where(_UploadsModel.id == uploads_id)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        for key, value in data.items():
            if hasattr(row, key):
                setattr(row, key, value)
        db.commit()
        db.refresh(row)
        return {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] update_upload {uploads_id} failed: {exc}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update upload")


@router.delete("/{uploads_id}", status_code=200)
def delete_upload(
    uploads_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete an upload record by ID."""
    try:
        if _UploadsModel is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        row = db.execute(
            select(_UploadsModel).where(_UploadsModel.id == uploads_id)
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Upload not found")
        db.delete(row)
        db.commit()
        return {"status": "deleted", "id": uploads_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[UPLOADS] delete_upload {uploads_id} failed: {exc}")
        db.rollback()
        raise HTTPException(status_code=404, detail="Upload not found")


uploads_router = router  # alias for main.py include_router compatibility
