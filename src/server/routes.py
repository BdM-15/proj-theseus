"""
FastAPI route overrides for GovCon server.

Goal: keep LightRAG query behavior *fully default*, while ensuring document ingestion
uses RAG-Anything's intended multimodal parsing + insertion pipeline.

We only override ingestion endpoints:
- POST /insert
- POST /documents/upload (used by the LightRAG WebUI)
"""

import logging
import os
import shutil
import tempfile

from fastapi import UploadFile, File
from fastapi.responses import JSONResponse
from lightrag.api.config import global_args

logger = logging.getLogger(__name__)


async def _save_upload_to_tmp(file: UploadFile) -> tuple[str, str]:
    """Persist UploadFile to a temp path; return (tmp_path, safe_filename)."""
    temp_dir = tempfile.gettempdir()
    safe_filename = (file.filename or "uploaded").replace("/", "_").replace("\\", "_")
    file_path = os.path.join(temp_dir, safe_filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return file_path, safe_filename


def create_insert_endpoint(app, rag_instance) -> None:
    """Override LightRAG /insert to route ingestion through RAG-Anything."""

    async def insert(file: UploadFile = File(...)):
        logger.info("📥 /insert upload: %s", file.filename)
        file_path, _safe_filename = await _save_upload_to_tmp(file)
        try:
            ok = await rag_instance.process_document_complete_lightrag_api(
                file_path=file_path,
                output_dir=global_args.working_dir,
            )
            if not ok:
                return JSONResponse(
                    {"status": "error", "message": "Document processing failed"},
                    status_code=500,
                )
            return JSONResponse(
                {"status": "success", "message": f"Processed {file.filename}"},
                status_code=200,
            )
        except Exception as e:
            logger.error("❌ /insert failed: %s", e, exc_info=True)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        finally:
            try:
                os.unlink(file_path)
            except Exception:
                pass

    app.add_api_route("/insert", insert, methods=["POST"], response_class=JSONResponse)


def create_documents_upload_endpoint(app, rag_instance) -> None:
    """Override LightRAG WebUI /documents/upload to route ingestion through RAG-Anything."""

    async def documents_upload(file: UploadFile = File(...)):
        logger.info("📥 /documents/upload upload: %s", file.filename)
        file_path, _safe_filename = await _save_upload_to_tmp(file)
        try:
            ok = await rag_instance.process_document_complete_lightrag_api(
                file_path=file_path,
                output_dir=global_args.working_dir,
            )
            if not ok:
                return JSONResponse(
                    {"status": "error", "message": "Document processing failed"},
                    status_code=500,
                )
            return JSONResponse(
                {"status": "success", "message": f"Processed {file.filename}"},
                status_code=200,
            )
        except Exception as e:
            logger.error("❌ /documents/upload failed: %s", e, exc_info=True)
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        finally:
            try:
                os.unlink(file_path)
            except Exception:
                pass

    app.add_api_route(
        "/documents/upload",
        documents_upload,
        methods=["POST"],
        response_class=JSONResponse,
    )
