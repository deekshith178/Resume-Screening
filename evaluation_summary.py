import json
from pathlib import Path


def load_metrics(path: str = "evaluation_metrics.json") -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Metrics file not found: {path}. Run train_and_evaluate.py first.")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def print_summary(metrics: dict) -> None:
    print("=== Evaluation Summary ===")

    accuracy = metrics.get("accuracy")
    if accuracy is not None:
        print(f"Overall accuracy: {accuracy:.4f}")

    auc = metrics.get("roc_auc_macro_ovr")
    if auc is not None:
        print(f"ROC-AUC (macro, OVR): {auc:.4f}")

    print("\nPrecision@K:")
    for k, v in sorted(metrics.get("precision_at_k", {}).items(), key=lambda kv: int(kv[0])):
        print(f"  P@{k}: {v:.4f}")

    print("\nPer-class confusion (total / correct / misclassified):")
    per_class = metrics.get("per_class_confusion", {})
    if not per_class:
        print("  (no per-class confusion data available)")
    else:
        for cls, info in per_class.items():
            total = info.get("total", 0)
            correct = info.get("correct", 0)
            mis = info.get("misclassified", {})
            print(f"- {cls}:")
            print(f"    total:   {total}")
            print(f"    correct: {correct}")
            if mis:
                print("    misclassified:")
                for target_cls, count in mis.items():
                    print(f"      -> {target_cls}: {count}")
            else:
                print("    misclassified: (none)")


def main() -> None:
    metrics = load_metrics()
    print_summary(metrics)


if __name__ == "__main__":
    main()
