from __future__ import annotations

from sqlalchemy import select

from .database import get_session
from .models import Candidate, Job


def main() -> None:
    with get_session() as db:
        cand = db.execute(select(Candidate).where(Candidate.id == "cand_xyz")).scalar_one_or_none()
        if not cand:
            db.add(
                Candidate(
                    id="cand_xyz",
                    email="enrimedia6969@gmail.com",
                    name="xyz",
                    resume_path="tests/data/sample_resume.txt",
                    category="Data Science",
                )
            )
            print("Inserted demo candidate cand_xyz")
        else:
            print("Demo candidate cand_xyz already exists")

        job = db.execute(select(Job).where(Job.id == "oracle-ds-1")).scalar_one_or_none()
        if not job:
            db.add(
                Job(
                    id="oracle-ds-1",
                    title="Data Scientist",
                    category="Data Science",
                    required_skills="numpy,scipy",
                    min_years_experience=2.0,
                )
            )
            print("Inserted demo job oracle-ds-1")
        else:
            print("Demo job oracle-ds-1 already exists")


if __name__ == "__main__":
    main()
