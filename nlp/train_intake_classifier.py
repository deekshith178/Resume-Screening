"""Train a classifier on resume files using the ResumeIntakePipeline.

This script is an example of how to move from the NLP intake pipeline
(candidate_token) + feature_builder to an actual ML model.

Directory format (supervised, label-per-folder):

    data/
      data_scientist/
        resume1.pdf
        resume2.docx
      ml_engineer/
        resume3.pdf
        ...

Usage (from project root):

    python -m nlp.train_intake_classifier \
        --data-dir data/resumes_by_role \
        --output-model intake_classifier.joblib \
        --output-meta intake_classifier_metadata.json

The trained model is a scikit-learn LogisticRegression classifier
on top of the feature vectors from `nlp.feature_builder.build_feature_vector`.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from .resume_intake_pipeline import ResumeIntakePipeline
from .feature_builder import build_feature_vector


@dataclass
class TrainingConfig:
    data_dir: Path
    output_model: Path
    output_meta: Path
    max_files_per_label: int | None = None


def load_labeled_resumes(config: TrainingConfig) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Walk the data_dir and build (X, y, label_names).

    Expected structure: one subdirectory per label, containing resume files.
    """
    X_list: list[np.ndarray] = []
    y_list: list[int] = []
    labels: list[str] = []

    pipeline = ResumeIntakePipeline.with_defaults()

    for label_idx, label_dir in enumerate(sorted(config.data_dir.iterdir())):
        if not label_dir.is_dir():
            continue

        label_name = label_dir.name
        labels.append(label_name)

        files = [p for p in label_dir.iterdir() if p.is_file()]
        if config.max_files_per_label is not None:
            files = files[: config.max_files_per_label]

        for path in files:
            try:
                token = pipeline.process_file(path)
                vec = build_feature_vector(token)
            except Exception as exc:  # pragma: no cover - runtime safety
                # Skip problematic files but warn
                print(f"[WARN] Skipping {path} ({exc})")
                continue

            X_list.append(vec)
            y_list.append(label_idx)

    if not X_list:
        raise RuntimeError(f"No training samples found in {config.data_dir}")

    X = np.stack(X_list, axis=0)
    y = np.asarray(y_list, dtype="int64")
    return X, y, labels


def train_classifier(X: np.ndarray, y: np.ndarray) -> LogisticRegression:
    clf = LogisticRegression(max_iter=1000, multi_class="auto")
    clf.fit(X, y)
    return clf


def save_artifacts(
    model: LogisticRegression,
    labels: List[str],
    config: TrainingConfig,
) -> None:
    # Save model
    config.output_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, config.output_model)

    # Save metadata
    meta = {
        "labels": labels,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "data_dir": str(config.data_dir),
        "model_path": str(config.output_model),
    }
    config.output_meta.parent.mkdir(parents=True, exist_ok=True)
    with config.output_meta.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a classifier on resume files using ResumeIntakePipeline + feature_builder.",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory with subfolders per label containing resume files.",
    )
    parser.add_argument(
        "--output-model",
        type=str,
        default="intake_classifier.joblib",
        help="Path to write the trained classifier (joblib).",
    )
    parser.add_argument(
        "--output-meta",
        type=str,
        default="intake_classifier_metadata.json",
        help="Path to write metadata (JSON with label names, etc.).",
    )
    parser.add_argument(
        "--max-files-per-label",
        type=int,
        default=None,
        help="Optional cap on number of resumes per label (for quick experiments).",
    )

    args = parser.parse_args()
    config = TrainingConfig(
        data_dir=Path(args.data_dir),
        output_model=Path(args.output_model),
        output_meta=Path(args.output_meta),
        max_files_per_label=args.max_files_per_label,
    )

    print(f"Loading labeled resumes from {config.data_dir}...")
    X, y, labels = load_labeled_resumes(config)
    print(f"Loaded {len(X)} resumes across {len(labels)} labels: {labels}")

    print("Training LogisticRegression classifier on intake feature vectors...")
    model = train_classifier(X, y)

    print("Saving model and metadata...")
    save_artifacts(model, labels, config)

    print("Done.")
    print(f"  Model:   {config.output_model}")
    print(f"  Metadata:{config.output_meta}")


if __name__ == "__main__":  # pragma: no cover
    main()
