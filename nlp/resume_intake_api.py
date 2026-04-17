"""FastAPI API for the resume intake pipeline.

Exposes a single endpoint:
- POST /intake_resume : accepts a resume file upload and returns candidate_token JSON

Run with e.g.:
    uvicorn nlp.resume_intake_api:app --reload

Dependencies:
    pip install fastapi uvicorn
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile

from .resume_intake_pipeline import ResumeIntakePipeline


app = FastAPI(title="Resume Intake API", version="1.0.0")
pipeline = ResumeIntakePipeline.with_defaults()


@app.post("/intake_resume")
async def intake_resume(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Accept a resume file and return the candidate_token.

    Supported extensions: .pdf, .docx, .doc, .txt
    """
    filename = file.filename or "resume"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".pdf", ".docx", ".doc", ".txt"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    # Save to a cross-platform temporary path
    tmp_dir = Path(tempfile.gettempdir())
    tmp_path = tmp_dir / filename
    try:
        content = await file.read()
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(content)

        candidate_token = pipeline.process_file(tmp_path)
        return candidate_token
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                # Not critical if cleanup fails
                pass
