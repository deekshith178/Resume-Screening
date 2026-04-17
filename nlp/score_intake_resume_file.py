"""Score a single resume file using the ResumeIntakePipeline + trained classifier.

This script loads:
- a trained model (from `train_intake_classifier.py`), and
- its metadata (labels),
then runs the full intake pipeline on a resume file and prints
predicted label and class probabilities.

Usage (from project root):

    python -m nlp.score_intake_resume_file \
        --model intake_classifier.joblib \
        --meta intake_classifier_metadata.json \
        --resume path/to/resume.pdf
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np

from .resume_intake_pipeline import ResumeIntakePipeline
from .feature_builder import build_feature_vector


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score a resume file using the intake pipeline + trained classifier.",
    )
    parser.add_argument("--model", type=str, required=True, help="Path to trained joblib model.")
    parser.add_argument(
        "--meta",
        type=str,
        required=True,
        help="Path to metadata JSON produced by train_intake_classifier.",
    )
    parser.add_argument("--resume", type=str, required=True, help="Path to resume file to score.")

    args = parser.parse_args()

    model_path = Path(args.model)
    meta_path = Path(args.meta)
    resume_path = Path(args.resume)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata not found: {meta_path}")
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {resume_path}")

    # Load model and metadata
    model = joblib.load(model_path)
    with meta_path.open("r", encoding="utf-8") as f:
        meta = json.load(f)

    labels = meta.get("labels")
    if not isinstance(labels, list) or not labels:
        raise ValueError("Metadata must contain a non-empty 'labels' list.")

    pipeline = ResumeIntakePipeline.with_defaults()

    print(f"Running intake pipeline on {resume_path}...")
    token = pipeline.process_file(resume_path)
    vec = build_feature_vector(token)

    # Predict probabilities
    probs = model.predict_proba(vec.reshape(1, -1))[0]
    pred_idx = int(np.argmax(probs))
    pred_label = labels[pred_idx] if 0 <= pred_idx < len(labels) else "(unknown)"

    print(f"\nPredicted label: {pred_label}")
    print("Class probabilities:")
    for idx, (lab, p) in enumerate(zip(labels, probs)):
        print(f"  [{idx}] {lab}: {p:.4f}")


if __name__ == "__main__":  # pragma: no cover
    main()
