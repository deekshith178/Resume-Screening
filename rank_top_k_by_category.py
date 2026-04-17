import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ml_pipeline import ResumeMLPipeline


def load_weights(weights_path: str | None):
    """Load learned weights from JSON if provided, else return Nones."""
    if not weights_path:
        return None, None, None, None
    wf = Path(weights_path)
    if not wf.exists():
        raise FileNotFoundError(f"Weights file not found: {weights_path}")
    with wf.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if "weights" in data:
        weights = data["weights"]
    else:
        weights = data
    w_S = float(weights.get("w_S")) if "w_S" in weights else None
    w_E = float(weights.get("w_E")) if "w_E" in weights else None
    w_P = float(weights.get("w_P")) if "w_P" in weights else None
    w_C = float(weights.get("w_C")) if "w_C" in weights else None
    if None in (w_S, w_E, w_P, w_C):
        return None, None, None, None
    return w_S, w_E, w_P, w_C


def _semantic_fit_phrase(S: float, category: str) -> str:
    if S >= 0.95:
        return f"very strong semantic fit for {category}"
    if S >= 0.9:
        return f"strong semantic alignment with {category}"
    if S >= 0.8:
        return f"good alignment with {category}"
    return f"some alignment with {category}"


def _level_phrase(value: float) -> str:
    """Map a normalized feature value in [0, 1] to a qualitative phrase."""
    if value >= 0.9:
        return "very high"
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "moderate"
    if value >= 0.25:
        return "limited"
    return "minimal"


def describe_candidate(row: pd.Series, df_row: pd.Series) -> str:
    """Build a short human-readable description for a selected candidate."""
    resume_id = int(row["resume_id"])
    category = str(row["category"])
    score = float(row["score"])
    S = float(row["S"])
    E_norm = float(row["E_norm"])
    P_norm = float(row["P_norm"])
    C_norm = float(row["C_norm"])

    years = float(df_row.get("years_experience", 0.0))
    projects = int(df_row.get("projects_count", 0))
    certs = int(df_row.get("certificates_count", 0))

    raw_text = str(df_row.get("resume_text", "")).strip().replace("\n", " ")
    snippet = raw_text
    if len(snippet) > 200:
        truncated = snippet[:200]
        # Avoid cutting in the middle of a word if possible
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]
        snippet = truncated + "..."

    semantic_phrase = _semantic_fit_phrase(S, category)
    exp_phrase = _level_phrase(E_norm)
    proj_phrase = _level_phrase(P_norm)
    cert_phrase = _level_phrase(C_norm)

    parts: list[str] = []
    parts.append(
        f"Resume {resume_id} ({category}) — overall score {score:.1f} with "
        f"{semantic_phrase}."
    )
    parts.append(
        f"Experience: {exp_phrase} (~{years:.1f} years). "
        f"Projects: {proj_phrase} (about {projects} projects). "
        f"Certifications: {cert_phrase} (around {certs} certificates)."
    )
    if snippet:
        parts.append(f"Profile snippet: \"{snippet}\"")

    return " " .join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rank top-K resumes per category using the unified dataset and "
            "ResumeMLPipeline."
        ),
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="If provided, only show top-K for this category (e.g., 'Data Science').",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=5,
        help="Number of top candidates to show per category (default: 5).",
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
        "--describe",
        action="store_true",
        help=(
            "If set, print a short natural-language description for each "
            "selected candidate."
        ),
    )

    args = parser.parse_args()

    # Load unified dataset
    unified_path = "unified_resume_dataset.csv"
    df = pd.read_csv(unified_path)

    text_col = "resume_text"
    label_col = "category"

    texts = df[text_col].astype(str).tolist()
    labels = df[label_col].astype(str).values

    pipeline = ResumeMLPipeline()

    # Semantic + structured features
    semantic_vecs = pipeline.encode_texts(texts)
    structured_vecs = pipeline.build_structured_features(df)
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # Fit clusters; centroids will be ordered by sorted unique labels
    pipeline.fit_clusters(final_vectors, labels=pd.Series(labels))

    unique_labels = sorted(np.unique(labels))
    label_to_idx = {lab: i for i, lab in enumerate(unique_labels)}

    # Load weights if provided
    w_S, w_E, w_P, w_C = load_weights(args.weights_path)

    rows = []
    for i in range(len(final_vectors)):
        vec = final_vectors[i]
        sims, sims_norm = pipeline.skill_similarity(vec)
        lab = labels[i]
        idx = label_to_idx[lab]
        S = float(sims_norm[idx])
        E_norm, P_norm, C_norm = structured_vecs[i]

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

        rows.append(
            {
                "resume_id": df.get("resume_id", pd.Series(range(1, len(df) + 1)))[i],
                "category": lab,
                "score": score,
                "S": S,
                "E_norm": float(E_norm),
                "P_norm": float(P_norm),
                "C_norm": float(C_norm),
                "row_index": i,
            }
        )

    ranked = pd.DataFrame(rows)

    # Choose which categories to show
    if args.category:
        cats = [args.category]
    else:
        cats = sorted(ranked["category"].unique())

    for cat in cats:
        sub = (
            ranked[ranked["category"] == cat]
            .sort_values("score", ascending=False)
            .head(args.k)
        )
        if sub.empty:
            continue
        print(f"=== Top {args.k} for category: {cat} ===")
        print(sub[["resume_id", "score", "S", "E_norm", "P_norm", "C_norm"]].to_string(index=False))
        print()

        if args.describe:
            print("Short descriptions:")
            for _, row in sub.iterrows():
                idx = int(row["row_index"])
                df_row = df.iloc[idx]
                desc = describe_candidate(row, df_row)
                print(f"- {desc}")
            print()


if __name__ == "__main__":
    main()