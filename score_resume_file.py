import argparse
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv

from ml_pipeline import ResumeMLPipeline
from nlp.nlp_intake import NLPIntakePipeline
from guidance_engine import GuidanceEngine

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# SERP API key for guidance engine (loaded from .env file)
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def train_pipeline() -> tuple[ResumeMLPipeline, list[str]]:
    """Train the ML pipeline on the unified dataset and return (pipeline, category_names)."""

    unified_path = "unified_resume_dataset.csv"
    df = pd.read_csv(unified_path)

    text_col = "resume_text"
    label_col = "category"

    texts = df[text_col].astype(str).tolist()
    labels = df[label_col]

    categories = sorted(labels.unique().tolist())

    pipeline = ResumeMLPipeline()

    # Semantic features
    semantic_vecs = pipeline.encode_texts(texts)

    # Structured features (fits the scaler)
    structured_vecs = pipeline.build_structured_features(df)

    # Feature fusion
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # Clustering
    pipeline.fit_clusters(final_vectors, labels=labels)

    return pipeline, categories


def save_trained_pipeline(path: str, pipeline: ResumeMLPipeline, categories: list[str]) -> None:
    """Persist the trained pipeline and category list to disk for reuse."""
    joblib.dump((pipeline, categories), path)


def load_trained_pipeline(path: str) -> tuple[ResumeMLPipeline, list[str]]:
    """Load a previously saved pipeline and categories list from disk."""
    pipeline, categories = joblib.load(path)
    return pipeline, categories


def score_resume_file(
    pipeline: ResumeMLPipeline,
    categories: list[str],
    resume_path: str,
    w_S: float | None = None,
    w_E: float | None = None,
    w_P: float | None = None,
    w_C: float | None = None,
) -> dict:
    """Run NLP intake on a resume file and score it via the ML pipeline.

    Uses the NLPIntakePipeline to extract text, normalize skills, and infer
    structured features, then feeds those into ResumeMLPipeline.
    """

    nlp_pipeline = NLPIntakePipeline(model_name="all-MiniLM-L6-v2")
    token = nlp_pipeline.build_candidate_token(resume_path)

    # Use the NLP embedding as semantic vector (SBERT with same model)
    semantic_vec = token.embedding

    # Use ML pipeline's scaler to normalize structured features
    structured_vec = pipeline.transform_structured_row(
        years_experience=token.experience,
        projects_count=token.projects,
        certificates_count=token.certifications,
    )

    # Fuse semantic + structured
    fused_vec = pipeline.fuse_features(
        semantic_vec.reshape(1, -1), structured_vec
    )[0]

    # Similarity to profession centroids
    sims, sims_norm = pipeline.skill_similarity(fused_vec)

    best_idx = int(np.argmax(sims_norm))
    S = float(sims_norm[best_idx])

    E_norm, P_norm, C_norm = structured_vec[0]

    # Use learned weights if provided
    if None not in (w_S, w_E, w_P, w_C):
        score = pipeline.compute_scores(
            S=S,
            E=E_norm,
            P=P_norm,
            C=C_norm,
            w_S=w_S,
            w_E=w_E,
            w_P=w_P,
            w_C=w_C,
        )
    else:
        score = pipeline.compute_scores(S=S, E=E_norm, P=P_norm, C=C_norm)

    is_hybrid, top1, top2, confidence = pipeline.detect_hybrid(sims)

    best_category = categories[best_idx] if 0 <= best_idx < len(categories) else "(unknown)"

    return {
        "path": resume_path,
        "best_category": best_category,
        "best_index": best_idx,
        "score": score,
        "normalized_similarity_best": S,
        "E_norm": float(E_norm),
        "P_norm": float(P_norm),
        "C_norm": float(C_norm),
        "is_hybrid": bool(is_hybrid),
        "top1_index": int(top1),
        "top2_index": int(top2),
        "confidence_gap": float(confidence),
        "skills": token.skills,
        "summary": token.summary,
        "name": token.name,
        "email": token.email,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end scoring: resume file -> NLP intake -> ML scoring "
            "(uses existing CSV training data)."
        ),
    )
    parser.add_argument("path", type=str, help="Path to resume file (pdf/docx/doc/txt)")
    parser.add_argument(
        "--model-path",
        type=str,
        default="trained_pipeline.joblib",
        help=(
            "Path to save/load trained ML pipeline (pipeline + categories) "
            "for reuse between runs."
        ),
    )
    parser.add_argument(
        "--reuse-model",
        action="store_true",
        help="Load an existing trained model from --model-path instead of retraining.",
    )
    parser.add_argument(
        "--weights-path",
        type=str,
        default=None,
        help=(
            "Optional path to JSON file with learned weights "
            "{w_S, w_E, w_P, w_C} (e.g., learned_weights.json)."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Print a human-friendly summary instead of raw JSON.",
    )

    args = parser.parse_args()

    model_path = args.model_path

    # Load or train ML pipeline
    if args.reuse_model and model_path and Path(model_path).exists():
        print(f"Loading ML pipeline from {model_path}...")
        pipeline, categories = load_trained_pipeline(model_path)
    else:
        print("Training ML pipeline on existing datasets (this may take a while)...")
        pipeline, categories = train_pipeline()
        if model_path:
            print(f"Saving trained ML pipeline to {model_path}...")
            save_trained_pipeline(model_path, pipeline, categories)

    print("Training complete. Running NLP intake and scoring...\n")

    w_S = w_E = w_P = w_C = None
    if args.weights_path is not None:
        weights_file = Path(args.weights_path)
        if not weights_file.exists():
            raise FileNotFoundError(
                f"Weights file not found: {args.weights_path}. "
                "Run learn_weights_example.py first or provide a valid path."
            )
        with weights_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Support either flat dict or {weights, metadata}
        if "weights" in data:
            weights = data["weights"]
            metadata = data.get("metadata", {})
        else:
            weights = data
            metadata = {}

        w_S = float(weights.get("w_S")) if "w_S" in weights else None
        w_E = float(weights.get("w_E")) if "w_E" in weights else None
        w_P = float(weights.get("w_P")) if "w_P" in weights else None
        w_C = float(weights.get("w_C")) if "w_C" in weights else None

        if metadata:
            print("Using learned weights with metadata:")
            for k, v in metadata.items():
                print(f"  {k}: {v}")

    result = score_resume_file(
        pipeline,
        categories,
        args.path,
        w_S=w_S,
        w_E=w_E,
        w_P=w_P,
        w_C=w_C,
    )

    if args.pretty:
        print("=== Resume Scoring Summary ===")
        print(f"File: {result['path']}")
        print(f"Best category: {result['best_category']} (index {result['best_index']})")
        print(f"Score: {result['score']:.2f} / 100")
        print(f"Normalized similarity to best category: {result['normalized_similarity_best']:.4f}")
        print("Structured features (normalized):")
        print(f"  Experience (E_norm):   {result['E_norm']:.4f}")
        print(f"  Projects (P_norm):     {result['P_norm']:.4f}")
        print(f"  Certificates (C_norm): {result['C_norm']:.4f}")
        print(f"Hybrid candidate: {'YES' if result['is_hybrid'] else 'NO'}")
        print(f"Confidence gap (top1 - top2 similarity): {result['confidence_gap']:.4f}")
        if result.get("skills"):
            skills_preview = ", ".join(result["skills"][:10])
            print(f"Top normalized skills: {skills_preview}")
        if result.get("summary"):
            print("Summary snippet:")
            print("  " + result["summary"][:200].replace("\n", " ") + ("..." if len(result["summary"]) > 200 else ""))

        # Guidance Engine: missing skills + suggested resources
        if result.get("skills"):
            print("\nGuidance (missing core skills and learning resources):")
            ge = GuidanceEngine(serpapi_key=SERPAPI_KEY)
            # We don't have the full CandidateToken here, but skills + summary are enough
            # for missing skill computation; we call generate_guidance via a minimal shim.
            # Reuse NLP intake for full tokens when needed.
            # For now, we just compute missing skills based on normalized skills.
            from nlp.nlp_intake import CandidateToken  # local import to avoid cycles
            import numpy as _np

            dummy_token = CandidateToken(
                embedding=_np.zeros(1, dtype=_np.float32),
                skills=result["skills"],
                experience=0.0,
                projects=0.0,
                certifications=0.0,
                education=0,
                summary=result.get("summary", ""),
                raw_text="",
            )
            g_res = ge.generate_guidance(dummy_token, result["best_category"], top_n=10)
            if g_res.missing_skills:
                print("  Missing core skills:")
                for skill in g_res.missing_skills:
                    print(f"    - {skill}")
                    urls = g_res.suggested_resources.get(skill, [])
                    if urls:
                        print(f"      Resources: {urls[0]}")
            else:
                print("  No major core skills missing for this category (based on current matrix).")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
