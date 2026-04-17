"""
New endpoint for batch resume upload and processing.
Add this to backend/main.py after the existing endpoints.
"""

from fastapi import File, UploadFile, Form

@app.post("/batch-process-resumes")
async def batch_process_resumes(
    files: List[UploadFile] = File(...),
    job_id: str = Form(...),
    recruiter: dict = Depends(get_current_recruiter),
):
    """
    Upload and process multiple resume files in batch.
    
    Args:
        files: List of resume files (PDF, DOCX, TXT)
        job_id: ID of the job to match candidates against
        recruiter: Current authenticated recruiter
    
    Returns:
        List of processed candidates with scores
    """
    from pathlib import Path
    import uuid
    import shutil
    
    # Validate job exists
    with get_session() as db:
        job = db.execute(select(Job).where(Job.id == job_id)).scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    # Create uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    results = []
    errors = []
    
    for file in files:
        try:
            # Save uploaded file
            file_ext = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = uploads_dir / unique_filename
            
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Run NLP intake
            nlp_pipeline = NLPIntakePipeline()
            token: CandidateToken = nlp_pipeline.build_candidate_token(str(file_path))
            
            # Score against all categories
            if _FILE_PIPELINE is None or _FILE_CATEGORIES is None:
                raise HTTPException(status_code=500, detail="ML pipeline not initialized")
            
            result = score_resume_file(
                _FILE_PIPELINE,
                _FILE_CATEGORIES,
                str(file_path),
            )
            
            # Create candidate
            candidate_id = f"cand_{uuid.uuid4().hex[:8]}"
            
            with get_session() as db:
                candidate = Candidate(
                    id=candidate_id,
                    name=token.name or "Unknown",
                    email=token.email or f"{candidate_id}@placeholder.com",
                    resume_path=str(file_path),
                    category=result["best_category"],
                    skills=json.dumps(result["skills"]),
                    summary=result["summary"],
                )
                db.add(candidate)
                db.commit()
                
                # Create score record for this job
                score_record = CandidateScore(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    score=result["best_score"],
                    breakdown=json.dumps(result.get("breakdown", {})),
                )
                db.add(score_record)
                db.commit()
            
            results.append({
                "filename": file.filename,
                "candidate_id": candidate_id,
                "name": token.name,
                "email": token.email,
                "score": result["best_score"],
                "category": result["best_category"],
                "status": "success"
            })
            
            # Log audit action
            _log_audit_action(
                action="process_resume",
                recruiter_id=recruiter.get("sub"),
                job_id=job_id,
                candidate_id=candidate_id,
                metadata={"filename": file.filename, "score": result["best_score"]}
            )
            
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e),
                "status": "error"
            })
    
    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "job_id": job_id
    }
