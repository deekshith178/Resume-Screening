import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

try:
    import umap
except ImportError:  # pragma: no cover - UMAP is optional
    umap = None

from ml_pipeline import ResumeMLPipeline


def train_and_get_vectors():
    """Train the pipeline and return labels, final_vectors, and centroids.

    Uses the unified_resume_dataset.csv file so it matches the main training
    and evaluation pipeline.
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

    pipeline.fit_clusters(final_vectors, labels=pd.Series(labels))

    return labels, final_vectors, pipeline.profession_centroids


def project_2d(vectors: np.ndarray, method: str = "pca", random_state: int = 42) -> np.ndarray:
    """Project high-dimensional vectors to 2D using PCA or UMAP."""
    if method == "umap":
        if umap is None:
            raise RuntimeError("UMAP is not installed; please install umap-learn or use method='pca'.")
        reducer = umap.UMAP(n_components=2, random_state=random_state)
        return reducer.fit_transform(vectors)

    # Default: PCA
    pca = PCA(n_components=2, random_state=random_state)
    return pca.fit_transform(vectors)


def plot_profession_zones(
    labels: np.ndarray,
    vectors_2d: np.ndarray,
    centroids_2d: np.ndarray,
    title: str = "Profession Zones",
    save_path: str | None = None,
) -> None:
    """Plot candidates and centroids in 2D space."""
    plt.figure(figsize=(10, 8))

    # Encode labels as integers for coloring
    unique_labels = np.unique(labels)
    label_to_idx = {lab: i for i, lab in enumerate(unique_labels)}
    label_indices = np.array([label_to_idx[lab] for lab in labels])

    scatter = plt.scatter(
        vectors_2d[:, 0],
        vectors_2d[:, 1],
        c=label_indices,
        cmap="tab20",
        alpha=0.6,
        s=15,
        label="Candidates",
    )

    # Plot centroids as stars
    plt.scatter(
        centroids_2d[:, 0],
        centroids_2d[:, 1],
        c="black",
        marker="*",
        s=200,
        edgecolors="white",
        linewidths=1.0,
        label="Centroids",
    )

    # Legend with category labels
    handles, _ = scatter.legend_elements()
    legend_labels = [str(lab) for lab in unique_labels]
    plt.legend(handles, legend_labels, title="Categories", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.title(title)
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
    else:
        plt.show()


def main() -> None:
    labels, final_vectors, centroids = train_and_get_vectors()

    # Combine candidate vectors and centroids so projection is consistent
    combined = np.vstack([final_vectors, centroids])

    # Try UMAP if available, otherwise PCA
    method = "umap" if umap is not None else "pca"
    combined_2d = project_2d(combined, method=method)

    vectors_2d = combined_2d[: len(final_vectors)]
    centroids_2d = combined_2d[len(final_vectors) :]

    plot_profession_zones(
        labels=labels,
        vectors_2d=vectors_2d,
        centroids_2d=centroids_2d,
        title=f"Profession Zones ({method.upper()})",
    )


if __name__ == "__main__":
    main()
