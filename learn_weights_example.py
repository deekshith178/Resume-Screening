import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

from ml_pipeline import ResumeMLPipeline, learn_weights_logistic


def main() -> None:
    """Example: compute S, E, P, C and learn weights with logistic regression.

    This script assumes you have added a binary `Selected` column to
    `resume_shortlisting_dataset_v2.csv`, where 1 = selected, 0 = not selected
    for each candidate row.
    """

    resumes_path = "UpdatedResumeDataSet_cleaned.csv"
    structured_path = "resume_shortlisting_dataset_v2.csv"

    resumes_df = pd.read_csv(resumes_path)
    structured_df = pd.read_csv(structured_path)

    if "Selected" not in structured_df.columns:
        raise ValueError(
            "Column 'Selected' not found in resume_shortlisting_dataset_v2.csv. "
            "Add a binary Selected column (1=selected, 0=not selected) before running this script."
        )

    # Align datasets by minimum length to allow row-wise fusion
    n = min(len(resumes_df), len(structured_df))
    resumes_df = resumes_df.iloc[:n].reset_index(drop=True)
    structured_df = structured_df.iloc[:n].reset_index(drop=True)

    # Text + label columns
    text_col = "Resume"
    label_col = "Category"

    texts = resumes_df[text_col].astype(str).tolist()
    labels = resumes_df[label_col]

    pipeline = ResumeMLPipeline()

    # 1) Semantic features
    semantic_vecs = pipeline.encode_texts(texts)

    # 2) Structured features (normalized E, P, C)
    structured_vecs = pipeline.build_structured_features(structured_df)

    # 3) Fuse
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # 4) Fit clusters/centroids using Category labels
    pipeline.fit_clusters(final_vectors, labels=labels)

    # 5) Build S, E, P, C arrays
    S_list = []
    E_list = []
    P_list = []
    C_list = []

    for i in range(final_vectors.shape[0]):
        vec = final_vectors[i]

        # skill similarity vs centroids
        sims, sims_norm = pipeline.skill_similarity(vec)
        S = float(sims_norm.max())  # best normalized similarity

        # normalized structured features
        E_norm, P_norm, C_norm = structured_vecs[i]

        S_list.append(S)
        E_list.append(float(E_norm))
        P_list.append(float(P_norm))
        C_list.append(float(C_norm))

    S_arr = np.array(S_list)
    E_arr = np.array(E_list)
    P_arr = np.array(P_list)
    C_arr = np.array(C_list)

    # 6) Binary labels for training weights
    y = structured_df["Selected"].astype(int).values

    # 7) Learn weights
    result = learn_weights_logistic(S_arr, E_arr, P_arr, C_arr, y)

    print("Raw logistic weights (normalized):")
    print(f"  w_S (skills similarity): {result['w_S']:.4f}")
    print(f"  w_E (experience):        {result['w_E']:.4f}")
    print(f"  w_P (projects):          {result['w_P']:.4f}")
    print(f"  w_C (certificates):      {result['w_C']:.4f}")

    # Blend learned weights with prior defaults to avoid overemphasizing experience.
    # Prior from development plan: [0.50, 0.25, 0.15, 0.10]
    prior = np.array([0.50, 0.25, 0.15, 0.10], dtype=float)
    lr = np.array([
        result["w_S"],
        result["w_E"],
        result["w_P"],
        result["w_C"],
    ], dtype=float)
    # alpha controls how much we trust the learned weights vs prior
    # alpha=0.3 → 30% learned signal, 70% prior
    alpha = 0.3
    blended = alpha * lr + (1.0 - alpha) * prior
    blended = blended / blended.sum()
    result["w_S"], result["w_E"], result["w_P"], result["w_C"] = blended.tolist()

    print("Blended weights (prior + learned):")
    print(f"  w_S (skills similarity): {result['w_S']:.4f}")
    print(f"  w_E (experience):        {result['w_E']:.4f}")
    print(f"  w_P (projects):          {result['w_P']:.4f}")
    print(f"  w_C (certificates):      {result['w_C']:.4f}")

    # 8) Persist weights to JSON for use in scoring scripts
    weights_path = Path("learned_weights.json")
    weights_only = {k: float(v) for k, v in result.items() if k.startswith("w_")}
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "resumes_path": resumes_path,
        "structured_path": structured_path,
        "num_samples": int(n),
    }
    to_save = {
        "weights": weights_only,
        "metadata": metadata,
    }
    with weights_path.open("w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2)
    print(f"\nWeights (with metadata) written to {weights_path}")


if __name__ == "__main__":
    main()
