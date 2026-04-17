import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml_pipeline import ResumeMLPipeline


def train_pipeline() -> tuple[ResumeMLPipeline, list[str]]:
    """Train the pipeline on the unified dataset and return the fitted instance and Category names.

    The Category names are sorted to match the centroid indexing used in fit_clusters.
    """
    unified_path = "unified_resume_dataset.csv"
    df = pd.read_csv(unified_path)

    text_col = "resume_text"
    label_col = "category"

    texts = df[text_col].astype(str).tolist()
    labels = df[label_col]

    # Sorted unique Category names; order matches centroid indices
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


def score_single_resume(
    pipeline: ResumeMLPipeline,
    resume_text: str,
    years_experience: float,
    projects_count: float,
    certificates_count: float,
    w_S: float | None = None,
    w_E: float | None = None,
    w_P: float | None = None,
    w_C: float | None = None,
) -> dict:
    """Compute the overall score and related info for a single resume."""
    # Semantic vector
    semantic_vec = pipeline.encode_texts([resume_text])[0]

    # Structured vector (normalized)
    structured_vec = pipeline.transform_structured_row(
        years_experience=years_experience,
        projects_count=projects_count,
        certificates_count=certificates_count,
    )

    # Fuse
    fused_vec = pipeline.fuse_features(
        semantic_vec.reshape(1, -1), structured_vec
    )[0]

    # Similarity to profession centroids
    sims, sims_norm = pipeline.skill_similarity(fused_vec)

    # Take best-matching profession similarity as S
    best_idx = int(np.argmax(sims_norm))
    S = float(sims_norm[best_idx])

    # Extract normalized structured features
    E_norm, P_norm, C_norm = structured_vec[0]

    # Use learned weights if provided, else defaults from compute_scores
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

    # Hybrid detection
    is_hybrid, top1, top2, confidence = pipeline.detect_hybrid(sims)

    return {
        "score": score,
        "best_profession_index": best_idx,
        "similarities": sims.tolist(),
        "normalized_similarity": sims_norm.tolist(),
        "E_norm": float(E_norm),
        "P_norm": float(P_norm),
        "C_norm": float(C_norm),
        "is_hybrid": bool(is_hybrid),
        "top1_index": int(top1),
        "top2_index": int(top2),
        "confidence_gap": float(confidence),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score new resumes using the trained ResumeMLPipeline.",
    )
    parser.add_argument("--text", required=True, help="Raw resume text to score")
    parser.add_argument("--years", type=float, required=True, help="Years of experience")
    parser.add_argument(
        "--projects",
        type=float,
        required=True,
        help="Number of projects completed",
    )
    parser.add_argument(
        "--certificates",
        type=float,
        required=True,
        help="Number of relevant certificates",
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

    args = parser.parse_args()

    print("Training pipeline on existing datasets (this may take a while)...")
    pipeline, categories = train_pipeline()
    print("Training complete. Scoring new resume...\n")

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

        # Backwards/forward compatible: support either flat dict or {weights, metadata}
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

    result = score_single_resume(
        pipeline,
        resume_text=args.text,
        years_experience=args.years,
        projects_count=args.projects,
        certificates_count=args.certificates,
        w_S=w_S,
        w_E=w_E,
        w_P=w_P,
        w_C=w_C,
    )

    best_idx = result["best_profession_index"]
    best_category = categories[best_idx] if 0 <= best_idx < len(categories) else "(unknown)"

    print(f"Overall score: {result['score']:.2f} / 100")
    print(f"Best-matching profession index: {best_idx} ({best_category})")
    print(f"Normalized similarity to best profession: {max(result['normalized_similarity']):.4f}")
    print("Structured features (normalized):")
    print(f"  Experience (E_norm):   {result['E_norm']:.4f}")
    print(f"  Projects (P_norm):     {result['P_norm']:.4f}")
    print(f"  Certificates (C_norm): {result['C_norm']:.4f}")
    print("Hybrid candidate:", "YES" if result["is_hybrid"] else "NO")
    print(f"Confidence gap (top1 - top2 similarity): {result['confidence_gap']:.4f}")


if __name__ == "__main__":
    main()
