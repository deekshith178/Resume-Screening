"""Hybrid scoring for a single resume file.

This script combines:

1. The existing CSV-based ML pipeline (ResumeMLPipeline) from ml_pipeline/score_new_resumes
   - Uses centroids + structured features + weights to compute a 0–100 score.

2. The intake-based classifier trained on resume files
   - Uses ResumeIntakePipeline + feature_builder + LogisticRegression
     (from train_intake_classifier.py).

Given a resume file, it:
- Runs the intake pipeline to extract candidate_token.
- Uses that text/structure to score via ResumeMLPipeline (Flow A).
- Uses the same candidate_token to build features for the intake classifier (Flow B).
- Prints both scores/labels and a simple combined "hybrid" score.

Usage (from project root):

    python -m nlp.hybrid_score_intake_resume \
        --resume path/to/resume.pdf \
        --weights-path learned_weights.json  # optional, for Flow A weights \
        --clf-model intake_classifier.joblib  # optional, for Flow B classifier \
        --clf-meta intake_classifier_metadata.json

If no classifier/model is provided, only Flow A (ResumeMLPipeline) is used.
If no weights are provided, Flow A falls back to default weights.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

import score_new_resumes
from ml_pipeline import ResumeMLPipeline
from nlp.feature_builder import build_feature_vector
from nlp.resume_intake_pipeline import FeatureScalerConfig, ResumeIntakePipeline


def _load_pipeline_from_csv() -> tuple[ResumeMLPipeline, list[str]]:
    """Train ResumeMLPipeline on CSV datasets using score_new_resumes.train_pipeline.

    Returns the fitted pipeline and the list of Category names (for reference).
    """
    print("Training ResumeMLPipeline on existing CSV datasets (Flow A)...")
    pipeline, categories = score_new_resumes.train_pipeline()
    print("Flow A pipeline training complete.\n")
    return pipeline, categories


def _load_intake_classifier(
    model_path: Optional[Path], meta_path: Optional[Path]
):
    """Load intake-based classifier and its labels if paths are provided.

    Returns (model, labels) or (None, None) if not provided.
    """
    if model_path is None or meta_path is None:
        return None, None

    if not model_path.exists():
        raise FileNotFoundError(f"Classifier model not found: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Classifier metadata not found: {meta_path}")

    model = joblib.load(model_path)
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)
    labels = meta.get("labels")
    if not isinstance(labels, list) or not labels:
        raise ValueError("Classifier metadata must contain a non-empty 'labels' list.")

    print("Loaded intake classifier with labels:", labels)
    return model, labels


def _load_flow_a_weights(weights_path: Optional[Path]):
    """Load Flow A weights (w_S, w_E, w_P, w_C) if provided.

    Supports both formats:
    - flat dict {"w_S": ..., ...}
    - {"weights": {"w_S": ...}, "metadata": {...}}
    """
    if weights_path is None:
        return None, None, None, None

    if not weights_path.exists():
        raise FileNotFoundError(
            f"Weights file not found: {weights_path}. "
            "Run learn_weights_example.py first or provide a valid path."
        )

    with weights_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "weights" in data:
        weights = data["weights"]
        metadata = data.get("metadata", {})
    else:
        weights = data
        metadata = {}

    if metadata:
        print("Using Flow A learned weights with metadata:")
        for k, v in metadata.items():
            print(f"  {k}: {v}")

    w_S = float(weights.get("w_S")) if "w_S" in weights else None
    w_E = float(weights.get("w_E")) if "w_E" in weights else None
    w_P = float(weights.get("w_P")) if "w_P" in weights else None
    w_C = float(weights.get("w_C")) if "w_C" in weights else None

    return w_S, w_E, w_P, w_C


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Hybrid scoring for a resume file using both the CSV-based ResumeMLPipeline "
            "(Flow A) and the intake-based classifier (Flow B)."
        ),
    )
    parser.add_argument("--resume", type=str, required=True, help="Path to resume file to score.")
    parser.add_argument(
        "--weights-path",
        type=str,
        default=None,
        help=(
            "Optional path to JSON file with Flow A learned weights {w_S, w_E, w_P, w_C} "
            "(e.g., learned_weights.json)."
        ),
    )
    parser.add_argument(
        "--clf-model",
        type=str,
        default=None,
        help="Optional path to intake classifier model (joblib).",
    )
    parser.add_argument(
        "--clf-meta",
        type=str,
        default=None,
        help="Optional path to intake classifier metadata JSON (labels).",
    )

    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")

    weights_path = Path(args.weights_path) if args.weights_path else None
    clf_model_path = Path(args.clf_model) if args.clf_model else None
    clf_meta_path = Path(args.clf_meta) if args.clf_meta else None

    # 1) Train/load Flow A pipeline from CSV datasets
    pipeline, csv_categories = _load_pipeline_from_csv()

    # 2) Load Flow A weights (optional)
    w_S, w_E, w_P, w_C = _load_flow_a_weights(weights_path)

    # 3) Load Flow B classifier (optional)
    clf_model, clf_labels = _load_intake_classifier(clf_model_path, clf_meta_path)

    # 4) Run intake pipeline on the resume file to get candidate_token
    intake_pipeline = ResumeIntakePipeline.with_defaults()
    print(f"\nRunning intake pipeline on {resume_path} (Flow B feature extraction)...")
    token = intake_pipeline.process_file(resume_path)

    # For Flow A, we need resume text + approximated raw structured features
    resume_text = token.get("raw_text", "")

    # Approximate raw numeric features from normalized values used by intake pipeline.
    # Intake pipeline uses FeatureScalerConfig for max ranges; we invert that.
    cfg = FeatureScalerConfig()
    years_experience_raw = float(token.get("experience", 0.0)) * cfg.max_experience_years
    projects_raw = float(token.get("projects", 0.0)) * cfg.max_projects
    certs_raw = float(token.get("certifications", 0.0)) * cfg.max_certifications

    # 5) Flow A scoring via existing score_new_resumes.score_single_resume
    print("\n[Flow A] Scoring via CSV-based ResumeMLPipeline...")
    flow_a_result = score_new_resumes.score_single_resume(
        pipeline,
        resume_text=resume_text,
        years_experience=years_experience_raw,
        projects_count=projects_raw,
        certificates_count=certs_raw,
        w_S=w_S,
        w_E=w_E,
        w_P=w_P,
        w_C=w_C,
    )

    best_idx_a = flow_a_result["best_profession_index"]
    best_category_a = (
        csv_categories[best_idx_a] if 0 <= best_idx_a < len(csv_categories) else "(unknown)"
    )

    print(f"Flow A - Overall score: {flow_a_result['score']:.2f} / 100")
    print(f"Flow A - Best-matching profession index: {best_idx_a} ({best_category_a})")
    print(
        "Flow A - Normalized similarity to best profession:",
        f"{max(flow_a_result['normalized_similarity']):.4f}",
    )
    print("Flow A - Structured features (normalized):")
    print(f"  Experience (E_norm):   {flow_a_result['E_norm']:.4f}")
    print(f"  Projects (P_norm):     {flow_a_result['P_norm']:.4f}")
    print(f"  Certificates (C_norm): {flow_a_result['C_norm']:.4f}")
    print("Flow A - Hybrid candidate:", "YES" if flow_a_result["is_hybrid"] else "NO")
    print(f"Flow A - Confidence gap (top1 - top2 similarity): {flow_a_result['confidence_gap']:.4f}")

    # 6) Flow B scoring via intake classifier (if provided)
    flow_b_max_proba = None
    pred_label_b = None
    if clf_model is not None and clf_labels is not None:
        print("\n[Flow B] Scoring via intake-based classifier...")
        vec = build_feature_vector(token)
        probs = clf_model.predict_proba(vec.reshape(1, -1))[0]
        pred_idx_b = int(np.argmax(probs))
        pred_label_b = clf_labels[pred_idx_b] if 0 <= pred_idx_b < len(clf_labels) else "(unknown)"
        flow_b_max_proba = float(probs[pred_idx_b])

        print(f"Flow B - Predicted label: {pred_label_b}")
        print("Flow B - Class probabilities:")
        for idx, (lab, p) in enumerate(zip(clf_labels, probs)):
            print(f"  [{idx}] {lab}: {p:.4f}")

    # 7) Simple hybrid summary score
    # Normalize Flow A score to 0-1 and combine with Flow B max probability if available.
    flow_a_norm = flow_a_result["score"] / 100.0
    if flow_b_max_proba is not None:
        hybrid_score = 0.5 * flow_a_norm + 0.5 * flow_b_max_proba
        print("\n[Hybrid] Combined score (avg of Flow A score and Flow B max proba):")
        print(f"  Hybrid score: {hybrid_score:.4f}")
    else:
        print("\n[Hybrid] Only Flow A available (no intake classifier provided).")
        print(f"  Flow A normalized score: {flow_a_norm:.4f}")


if __name__ == "__main__":  # pragma: no cover
    main()
