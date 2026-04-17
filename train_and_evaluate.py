import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ml_pipeline import ResumeMLPipeline, precision_at_k


def train_pipeline(
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[ResumeMLPipeline, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Train the pipeline and return (pipeline, y_train, X_train, y_val, X_val).

    Uses the unified_resume_dataset.csv file.
    """
    unified_path = "unified_resume_dataset.csv"
    df = pd.read_csv(unified_path)

    text_col = "resume_text"
    label_col = "category"

    texts = df[text_col].astype(str).tolist()
    labels = df[label_col].values

    pipeline = ResumeMLPipeline()

    semantic_vecs = pipeline.encode_texts(texts)
    structured_vecs = pipeline.build_structured_features(df)
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # Split into train/validation so evaluation is on held-out data
    X_train, X_val, y_train, y_val = train_test_split(
        final_vectors,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    # Fit clusters/centroids on training data only
    pipeline.fit_clusters(X_train, labels=pd.Series(y_train))

    return pipeline, y_train, X_train, y_val, X_val


def evaluate(
    pipeline: ResumeMLPipeline,
    labels: np.ndarray,
    vectors: np.ndarray,
    log_path: str | None = None,
    plot_path: str | None = None,
) -> None:
    """Compute basic metrics using centroid similarity as scores.

    Optionally logs metrics to a JSON file and plots score distributions.
    """
    # Map labels to indices consistent with the centroids
    unique_labels = sorted(np.unique(labels))
    label_to_idx = {lab: i for i, lab in enumerate(unique_labels)}
    y_true_idx = np.array([label_to_idx[lab] for lab in labels])

    label_names = [str(lab) for lab in unique_labels]

    print("Label index -> Category mapping:")
    for idx, lab in enumerate(label_names):
        print(f"  {idx}: {lab}")

    # For each candidate vector, compute similarity to centroids
    sims_list = []
    preds_idx = []
    for vec in vectors:
        sims, _ = pipeline.skill_similarity(vec)
        sims_list.append(sims)
        preds_idx.append(int(np.argmax(sims)))

    sims_mat = np.vstack(sims_list)  # shape: (n_samples, n_centroids)
    y_pred_idx = np.array(preds_idx)

    # Accuracy and basic classification report
    acc = accuracy_score(y_true_idx, y_pred_idx)
    print(f"Accuracy (by nearest centroid): {acc:.4f}")
    print("\nClassification report (indices correspond to sorted Category labels):")
    print(classification_report(y_true_idx, y_pred_idx, target_names=label_names))

    # Confusion matrix
    cm = confusion_matrix(y_true_idx, y_pred_idx)
    print("Confusion matrix:")
    print(cm)

    # ROC-AUC (multiclass, using similarities as scores)
    # One-hot encode y_true
    n_classes = len(unique_labels)
    y_true_onehot = np.zeros((len(labels), n_classes), dtype=int)
    for i, idx in enumerate(y_true_idx):
        y_true_onehot[i, idx] = 1

    try:
        auc_macro = roc_auc_score(y_true_onehot, sims_mat, multi_class="ovr", average="macro")
        print(f"\nROC-AUC (macro, OVR): {auc_macro:.4f}")
    except ValueError:
        auc_macro = None
        print("\nROC-AUC not computed (likely due to single-class or degenerate labels).")

    # Precision@K for each class using similarity scores
    precision_at_k_values: dict[int, float] = {}
    for k in (1, 3, 5):
        # For simplicity, treat "relevant" as correct top-k prediction for the true class index
        relevance = (y_true_idx == y_pred_idx).astype(int)
        p_at_k = precision_at_k(relevance, sims_mat.max(axis=1), k=k)
        precision_at_k_values[k] = float(p_at_k)
        print(f"Precision@{k}: {p_at_k:.4f}")

    # Optionally log metrics to JSON
    if log_path is not None:
        report_dict = classification_report(
            y_true_idx,
            y_pred_idx,
            target_names=label_names,
            output_dict=True,
        )

        # Build compact per-class confusion summary
        per_class_confusion: dict[str, dict[str, int]] = {}
        for true_idx, true_name in enumerate(label_names):
            row = cm[true_idx]
            total = int(row.sum())
            correct = int(row[true_idx])
            misclassified: dict[str, int] = {}
            for pred_idx, count in enumerate(row):
                if pred_idx == true_idx or count == 0:
                    continue
                misclassified[label_names[pred_idx]] = int(count)
            per_class_confusion[true_name] = {
                "total": total,
                "correct": correct,
                "misclassified": misclassified,
            }

        metrics = {
            "accuracy": float(acc),
            "classification_report": report_dict,
            "confusion_matrix": cm.tolist(),
            "roc_auc_macro_ovr": auc_macro,
            "precision_at_k": {str(k): v for k, v in precision_at_k_values.items()},
            "label_index_mapping": {str(i): lab for i, lab in enumerate(label_names)},
            "per_class_confusion": per_class_confusion,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nMetrics written to {log_path}")

    # Optionally plot distribution of max similarity scores
    if plot_path is not None:
        max_scores = sims_mat.max(axis=1)

        # Overall distribution
        plt.figure(figsize=(6, 4))
        plt.hist(max_scores, bins=20, alpha=0.7, color="steelblue")
        plt.xlabel("Max similarity to any centroid")
        plt.ylabel("Count")
        plt.title("Distribution of max similarity scores (overall)")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150)
        plt.close()
        print(f"Score distribution plot saved to {plot_path}")

        # Per-class distributions (one subplot per Category)
        n_classes = len(label_names)
        n_cols = min(3, n_classes)
        n_rows = int(np.ceil(n_classes / n_cols))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows), squeeze=False)

        for idx, lab in enumerate(label_names):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row][col]

            class_mask = (y_true_idx == idx)
            class_scores = max_scores[class_mask]
            if class_scores.size == 0:
                ax.set_visible(False)
                continue

            ax.hist(class_scores, bins=15, alpha=0.7, color="seagreen")
            ax.set_title(f"{lab} (n={class_scores.size})")
            ax.set_xlabel("Max similarity")
            ax.set_ylabel("Count")

        # Hide any unused subplots
        for j in range(idx + 1, n_rows * n_cols):
            row = j // n_cols
            col = j % n_cols
            axes[row][col].set_visible(False)

        fig.tight_layout()
        per_class_path = plot_path.replace(".png", "_per_class.png")
        fig.savefig(per_class_path, dpi=150)
        plt.close(fig)
        print(f"Per-class score distribution plot saved to {per_class_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train ResumeMLPipeline and evaluate on a held-out validation set.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data to use for validation (default: 0.2)",
    )
    parser.add_argument(
        "--log-path",
        type=str,
        default="evaluation_metrics.json",
        help="Path to JSON file where evaluation metrics will be saved.",
    )
    parser.add_argument(
        "--plot-path",
        type=str,
        default="score_distribution.png",
        help="Path to PNG file where score distribution plot will be saved.",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="Disable writing metrics to a JSON file.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable writing score distribution plots to disk.",
    )
    args = parser.parse_args()

    pipeline, y_train, X_train, y_val, X_val = train_pipeline(test_size=args.test_size)

    log_path = None if args.no_log else args.log_path
    plot_path = None if args.no_plot else args.plot_path

    print(f"Evaluation on validation set (held-out, test_size={args.test_size:.2f}):")
    evaluate(pipeline, y_val, X_val, log_path=log_path, plot_path=plot_path)


if __name__ == "__main__":
    main()
