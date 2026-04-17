from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session
from backend.models import CandidateScore, Job, GuidanceOptIn, GuidanceRecommendation

def migrate_and_delete():
    engine = create_engine('sqlite:///./guidance_demo.db')
    
    source_job_id = "oracle-ds-1"
    target_job_id = "job-datascience"
    
    with Session(engine) as session:
        # 1. Get source scores
        source_scores = session.scalars(
            select(CandidateScore).where(CandidateScore.job_id == source_job_id)
        ).all()
        
        print(f"Found {len(source_scores)} scores for {source_job_id}.")
        
        migrated_count = 0
        skipped_count = 0
        
        for score in source_scores:
            # Check if exists in target
            existing = session.scalar(
                select(CandidateScore).where(
                    CandidateScore.candidate_id == score.candidate_id,
                    CandidateScore.job_id == target_job_id
                )
            )
            
            if existing:
                print(f"Candidate {score.candidate_id}: already exists in {target_job_id}. Deleting duplicate.")
                session.delete(score)
                skipped_count += 1
            else:
                print(f"Candidate {score.candidate_id}: migrating to {target_job_id}.")
                score.job_id = target_job_id
                migrated_count += 1
                
        # 2. Migrate GuidanceOptIn
        source_optins = session.scalars(
            select(GuidanceOptIn).where(GuidanceOptIn.job_id == source_job_id)
        ).all()
        print(f"Found {len(source_optins)} opt-ins for {source_job_id}.")
        
        for optin in source_optins:
            existing = session.scalar(
                select(GuidanceOptIn).where(
                    GuidanceOptIn.candidate_id == optin.candidate_id,
                    GuidanceOptIn.job_id == target_job_id
                )
            )
            if existing:
                session.delete(optin)
            else:
                optin.job_id = target_job_id

        # 3. Migrate GuidanceRecommendation
        source_recs = session.scalars(
            select(GuidanceRecommendation).where(GuidanceRecommendation.job_id == source_job_id)
        ).all()
        print(f"Found {len(source_recs)} recommendations for {source_job_id}.")
        
        for rec in source_recs:
            existing = session.scalar(
                select(GuidanceRecommendation).where(
                    GuidanceRecommendation.candidate_id == rec.candidate_id,
                    GuidanceRecommendation.job_id == target_job_id
                )
            )
            if existing:
                session.delete(rec)
            else:
                rec.job_id = target_job_id

        # 4. Delete the source job
        source_job = session.get(Job, source_job_id)
        if source_job:
            print(f"Deleting job {source_job_id}.")
            session.delete(source_job)
            
        session.commit()
        print(f"Migration complete: Scores migrated/deleted, Dependencies handled.")

if __name__ == "__main__":
    migrate_and_delete()
