import sys
import os

# Add current directory to path so we can import backend
sys.path.append(os.getcwd())

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from backend.models import CandidateScore

def fix_scores():
    engine = create_engine('sqlite:///./guidance_demo.db')
    
    with Session(engine) as session:
        # Find inflated scores (max possible correct score is 100)
        inflated_scores = session.scalars(
            select(CandidateScore).where(CandidateScore.score > 100)
        ).all()
        
        print(f"Found {len(inflated_scores)} inflated scores.")
        
        count = 0
        for score in inflated_scores:
            old_score = score.score
            # Normalize by 100 as weights summed to 100 instead of 1
            new_score = old_score / 100.0
            score.score = new_score
            print(f"Fixed {score.candidate_id}: {old_score:.2f} -> {new_score:.2f}")
            count += 1
            
        if count > 0:
            session.commit()
            print(f"\nSuccessfully corrected {count} scores.")
        else:
            print("No changes needed.")

if __name__ == "__main__":
    fix_scores()
