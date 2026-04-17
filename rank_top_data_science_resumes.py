import argparse

import pandas as pd
import numpy as np

from ml_pipeline import ResumeMLPipeline


def main(category: str = "Data Science", top_n: int = 2) -> None:
    # Load unified dataset (built from UpdatedResumeDataSet_cleaned.csv + structured features)
    df = pd.read_csv("unified_resume_dataset.csv")

    if "category" not in df.columns:
        raise RuntimeError("Expected 'category' column in unified_resume_dataset.csv")

    # Initialize pipeline and build full feature vectors for all resumes
    pipeline = ResumeMLPipeline()

    texts = df["resume_text"].astype(str).tolist()
    semantic_vecs = pipeline.encode_texts(texts)
    structured_vecs = pipeline.build_structured_features(df)
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # Fit clusters/centroids using all categories
    labels = df["category"].astype(str)
    pipeline.fit_clusters(final_vectors, labels=labels)

    # Map categories to centroid indices and find index for the requested category
    unique_labels = sorted(labels.unique())
    label_to_idx = {lab: i for i, lab in enumerate(unique_labels)}

    if category not in label_to_idx:
        raise RuntimeError(f"Category '{category}' not found in unified_resume_dataset.csv")

    category_idx = label_to_idx[category]

    # Structured features after normalization: columns correspond to E, P, C
    E = structured_vecs[:, 0]
    P = structured_vecs[:, 1]
    C = structured_vecs[:, 2]

    records: list[dict] = []
    for i, vec in enumerate(final_vectors):
        sims, sims_norm = pipeline.skill_similarity(vec)
        S = float(sims_norm[category_idx])
        score = float(pipeline.compute_scores(S, float(E[i]), float(P[i]), float(C[i])))

        records.append(
            {
                "resume_id": int(df.loc[i, "resume_id"]),
                "category": str(df.loc[i, "category"]),
                "score": score,
            }
        )

    scores_df = pd.DataFrame(records)

    # Filter to the requested category and sort by score descending
    cat_scores = scores_df[scores_df["category"] == category].sort_values(
        "score", ascending=False
    )

    top_resumes = cat_scores.head(top_n)

    print(f"Top {top_n} resumes for '{category}' (by model score):")
    for _, row in top_resumes.iterrows():
        rid = int(row["resume_id"])
        sc = float(row["score"])
        print(f"Resume ID: {rid}, Score: {sc:.2f}")
        # Print a short snippet of the resume text for context
        text = df.loc[df["resume_id"] == rid, "resume_text"].iloc[0]
        snippet = str(text)[:300].replace("\n", " ")
        print(f"Snippet: {snippet}...")
        print("-" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Rank resumes for a chosen profession and return the top N by model score.",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="Data Science",
        help="Profession/category to rank (must match the 'category' column).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=2,
        help="Number of top resumes to return (default: 2).",
    )
    args = parser.parse_args()

    main(category=args.category, top_n=args.top_n)
