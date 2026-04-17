# Development Tracker: Resume Shortlisting ML Model

This file tracks progress as we implement the ML pipeline described in `development_plan_ml_model.md`.

## Legend
- ✅ Completed
- 🔄 In progress
- ⏳ Not started

## Steps
1. Define implementation scope from `development_plan_ml_model.md` — ✅ Completed
2. Create `tracker.md` and log initial plan and steps — ✅ Completed
3. Create `requirements.txt` based on needed ML and data libraries — ✅ Completed
4. Install Python dependencies from `requirements.txt` — ✅ Attempted (hdbscan build failed; MSVC 14.0+ required)
5. Implement core ML pipeline script for resume shortlisting — ✅ Completed (see `ml_pipeline.py`)
6. Add guidance/test-fit utilities — ✅ Completed (k-NN guidance and job-fit scoring in `ResumeMLPipeline`)
7. Add basic evaluation routine — ✅ Basic `precision_at_k` helper added in `ml_pipeline.py`
8. Align ml_pipeline.py with actual CSV columns — ✅ Completed
9. Add score_new_resumes.py script for scoring new resumes — ✅ Completed
10. Add score_new_resumes.ipynb notebook for interactive scoring — ✅ Completed
11. Add visualization utilities for profession zones — ✅ Completed (see `visualize_embeddings.py`)
12. Add evaluation script for ML model — ✅ Completed (see `train_and_evaluate.py`)
13. Integrate optional HDBSCAN clustering path — ✅ Completed (configurable via `ResumeMLPipeline(clustering_method='hdbscan')`)

## Activity Log
- Step 2: `tracker.md` created and initial steps logged.
- Step 3: `requirements.txt` created with core ML/data libraries.
- Step 4: `pip install -r requirements.txt` run; most packages installed, `hdbscan` failed due to missing Microsoft C++ Build Tools (MSVC 14.0+).
- Step 5 & 6: Implemented `ResumeMLPipeline` in `ml_pipeline.py` with embedding, structured features, clustering, scoring, hybrid detection, k-NN guidance, and job-fit scoring.
- Step 7: Added simple `precision_at_k` evaluation helper in `ml_pipeline.py`.
- Step 8: Updated `ml_pipeline.py` to use `Category`/`Resume` columns and to derive numeric structured features from `Years of Experience`, `Projects`, and `Certificates`.
- Step 9: Created `score_new_resumes.py` to train the pipeline and score a single new resume from CLI.
- Step 10: Created `score_new_resumes.ipynb` notebook for interactive scoring experiments.
- Step 11: Created `visualize_embeddings.py` to project candidate tokens and centroids with PCA/UMAP and plot profession zones.
- Step 12: Created `train_and_evaluate.py` to train the pipeline and print metrics (accuracy, classification report, confusion matrix, ROC-AUC, precision@K).
- Step 13: Extended `ResumeMLPipeline` with an optional `clustering_method='hdbscan'` path (requires `hdbscan` to be installed).
- Review: Verified current implementation covers all major items from `development_plan_ml_model.md`, including visualization and evaluation.

## Notes / Next Ideas
- Once `hdbscan` actually installs successfully (after MSVC build tools), you can run with `clustering_method='hdbscan'` to compare clusters vs KMeans.
- Consider persisting trained embeddings, final vectors, and cluster model to disk (e.g., via `joblib`) to avoid retraining before each scoring run.
- Map profession indices back to human-readable categories using `Category` values so CLI/notebook outputs are easier to interpret.
