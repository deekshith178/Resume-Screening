import sys
import os
import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from backend.models import Candidate, CandidateScore, Job
from score_resume_file import load_trained_pipeline, score_resume_file

def backfill():
    print("Loading ML pipeline...")
    # Ensure trained pipeline exists
    if not os.path.exists("trained_pipeline.joblib"):
        print("Error: trained_pipeline.joblib not found. Cannot backfill.")
        return

    pipeline, categories = load_trained_pipeline("trained_pipeline.joblib")
    
    engine = create_engine('sqlite:///./guidance_demo.db')
    
    with Session(engine) as session:
        scores = session.scalars(select(CandidateScore)).all()
        print(f"Checking {len(scores)} scores...")
        
        updated_count = 0
        for s in scores:
            c = session.scalar(select(Candidate).where(Candidate.id == s.candidate_id))
            
            should_update = False
            # Check for empty components
            if not s.components_json or s.components_json == "{}":
                should_update = True
                
            # Check for Unknown name
            if c.name == "Unknown":
                should_update = True
                
            if should_update:
                print(f"Processing candidate {c.id} ({c.name})...")
                
                if not c.resume_path or not os.path.exists(c.resume_path):
                    print(f"  Skipping: resume path not found: {c.resume_path}")
                    continue
                
                try:
                    # Re-score using default weights (matches standard scoring)
                    result = score_resume_file(pipeline, categories, c.resume_path)
                    
                    # Update Components
                    s.components_json = json.dumps({
                        "normalized_similarity": result["normalized_similarity_best"],
                        "E_norm": result["E_norm"],
                        "P_norm": result["P_norm"],
                        "C_norm": result["C_norm"],
                    })
                    
                    # Update Score
                    s.score = result["score"]
                    
                    # Update Name if found
                    if result.get("name"):
                        print(f"  Found name: {result['name']}")
                        c.name = result["name"]
                        
                    # Update other metadata
                    if result.get("skills"):
                        c.skills = json.dumps(result["skills"])
                    
                    if result.get("summary"):
                        c.summary = result["summary"]

                    updated_count += 1
                    print("  Updated successfully.")
                    
                except Exception as e:
                    print(f"  Error re-scoring {c.id}: {e}")
                    
        if updated_count > 0:
            session.commit()
            print(f"\nSuccessfully backfilled {updated_count} candidates.")
        else:
            print("\nNo candidates required backfilling.")

if __name__ == "__main__":
    backfill()
