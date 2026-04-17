import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans

try:
    import hdbscan  # type: ignore[import]
except Exception:  # pragma: no cover - optional dependency
    hdbscan = None
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer


def precision_at_k(y_true: np.ndarray, scores: np.ndarray, k: int = 10) -> float:
    """Simple Precision@K over a binary relevance vector.

    This is a small placeholder aligned with the evaluation section of the plan.
    """
    if len(y_true) != len(scores):
        raise ValueError("y_true and scores must have same length")
    idx = np.argsort(scores)[::-1][:k]
    top_k_relevant = y_true[idx].sum()
    return float(top_k_relevant / max(k, 1))


def learn_weights_logistic(S: np.ndarray, E: np.ndarray, P: np.ndarray, C: np.ndarray,
                           y: np.ndarray) -> dict:
    """Learn scoring weights using logistic regression, as in the development plan.

    Parameters
    ----------
    S, E, P, C : np.ndarray
        1D arrays of the skill similarity and normalized structured features
        for each candidate.
    y : np.ndarray
        1D binary array of labels, e.g. 1 for "Selected" and 0 for "Not selected".

    Returns
    -------
    dict
        A dictionary containing normalized weights (w_S, w_E, w_P, w_C) and
        the fitted LogisticRegression model under the key "model".
    """
    if not (len(S) == len(E) == len(P) == len(C) == len(y)):
        raise ValueError("S, E, P, C, and y must have the same length")

    X = np.column_stack([S, E, P, C])
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, y)

    coefs = np.abs(clf.coef_[0])
    if coefs.sum() == 0:
        # Fallback to equal weights if model is degenerate
        weights = np.full(4, 1.0 / 4.0)
    else:
        weights = coefs / coefs.sum()

    return {
        "w_S": float(weights[0]),
        "w_E": float(weights[1]),
        "w_P": float(weights[2]),
        "w_C": float(weights[3]),
        "model": clf,
    }


class ResumeMLPipeline:
    """End-to-end ML pipeline as described in development_plan_ml_model.md."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", n_clusters: int | None = None,
                 clustering_method: str = "kmeans"):
        """Initialize the pipeline.

        clustering_method: "kmeans" (default) or "hdbscan" (if hdbscan is installed).
        """
        self.embedder = SentenceTransformer(model_name)
        self.n_clusters = n_clusters
        # Clamp normalized structured features to [0, 1] even for out-of-range values
        # so scoring remains interpretable and bounded.
        self.scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
        self.clustering_method = clustering_method
        self.cluster_model: KMeans | None = None
        self.profession_centroids: np.ndarray | None = None
        self.kNN: NearestNeighbors | None = None

    # 3.1 Resume Text Embedding
    def encode_texts(self, texts: list[str]) -> np.ndarray:
        return self.embedder.encode(texts, show_progress_bar=True)

    # 3.2 Structured Feature Vectorization
    def build_structured_features(self, df: pd.DataFrame) -> np.ndarray:
        """Fit scaler on structured features and return normalized values.

        Supports two main schemas:
        - Original structured schema (resume_shortlisting_dataset_v2.csv):
          ["Years of Experience", "Projects", "Certificates"]
        - Unified schema (unified_resume_dataset.csv):
          ["years_experience", "projects_count", "certificates_count"]
        """
        if {"Years of Experience", "Projects", "Certificates"}.issubset(df.columns):
            years = pd.to_numeric(df["Years of Experience"], errors="coerce").fillna(0.0)

            def _count_items(series: pd.Series) -> pd.Series:
                return series.fillna("").astype(str).apply(
                    lambda s: 0 if s.strip() == "" else len(s.split(","))
                )

            projects = _count_items(df["Projects"])
            certificates = _count_items(df["Certificates"])

            structured = pd.DataFrame(
                {
                    "years_experience": years.astype(float),
                    "projects_count": projects.astype(float),
                    "certificates_count": certificates.astype(float),
                }
            )
        else:
            # Unified or already numeric schema
            for cols in (
                ["years_experience", "projects_count", "certificates_count"],
                ["years_experience", "projects", "certificates"],
            ):
                if set(cols).issubset(df.columns):
                    structured = df[cols].fillna(0).astype(float)
                    break
            else:
                raise ValueError(
                    "DataFrame does not contain a recognized structured schema for "
                    "experience/projects/certificates."
                )

        self.scaler.fit(structured)
        return self.scaler.transform(structured)

    def transform_structured_row(
        self,
        years_experience: float,
        projects_count: float,
        certificates_count: float,
    ) -> np.ndarray:
        """Transform a single structured feature row using the fitted scaler."""
        if not hasattr(self.scaler, "min_"):
            raise RuntimeError("Scaler not fitted; call build_structured_features first.")
        arr = np.array([[years_experience, projects_count, certificates_count]], dtype=float)
        return self.scaler.transform(arr)

    # 3.3 Feature Fusion
    def fuse_features(self, semantic_vecs: np.ndarray, structured_vecs: np.ndarray) -> np.ndarray:
        return np.concatenate([semantic_vecs, structured_vecs], axis=1)

    # 4. Clustering Model (Profession Zones)
    def fit_clusters(self, final_vectors: np.ndarray, labels: pd.Series | None = None):
        if self.clustering_method == "hdbscan":
            if hdbscan is None:
                raise RuntimeError(
                    "HDBSCAN selected as clustering_method, but hdbscan is not installed.\n"
                    "Install hdbscan (and required build tools) or use clustering_method='kmeans'."
                )
            # HDBSCAN automatically finds clusters; n_clusters is ignored.
            self.cluster_model = hdbscan.HDBSCAN(min_cluster_size=15)
            cluster_ids = self.cluster_model.fit_predict(final_vectors)
        else:
            # Default: KMeans with fixed number of clusters.
            if self.n_clusters is None:
                if labels is not None:
                    self.n_clusters = labels.nunique()
                else:
                    self.n_clusters = 20
            self.cluster_model = KMeans(n_clusters=self.n_clusters, random_state=42)
            cluster_ids = self.cluster_model.fit_predict(final_vectors)

        if labels is not None:
            centroids = []
            for label in sorted(labels.unique()):
                mask = labels == label
                if mask.sum() == 0:
                    continue
                centroids.append(final_vectors[mask].mean(axis=0))
            self.profession_centroids = np.vstack(centroids)
        else:
            self.profession_centroids = self.cluster_model.cluster_centers_

        self.kNN = NearestNeighbors(n_neighbors=5).fit(final_vectors)
        return cluster_ids

    # 5.1 Skill Similarity (Semantic Matching)
    def skill_similarity(self, candidate_vec: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        if self.profession_centroids is None:
            raise RuntimeError("Clusters not fitted; call fit_clusters first.")
        sims = cosine_similarity(candidate_vec.reshape(1, -1), self.profession_centroids)[0]
        sims_norm = (sims + 1) / 2.0
        return sims, sims_norm

    # 5.2 Weighted Score Formula
    def compute_scores(self, S: float, E: float, P: float, C: float,
                       w_S: float = 0.5, w_E: float = 0.25,
                       w_P: float = 0.15, w_C: float = 0.10) -> float:
        return 100.0 * (w_S * S + w_E * E + w_P * P + w_C * C)

    # 6. Hybrid Candidate Detection
    def detect_hybrid(self, sims: np.ndarray, threshold: float = 0.1) -> tuple[bool, int, int, float]:
        idx_sorted = np.argsort(sims)[::-1]
        top1, top2 = idx_sorted[0], idx_sorted[1]
        confidence = abs(sims[top1] - sims[top2])
        return confidence < threshold, int(top1), int(top2), float(confidence)

    # 7. Guidance Model (k-NN Based)
    def nearest_neighbors(self, candidate_vec: np.ndarray, k: int = 5) -> np.ndarray:
        if self.kNN is None:
            raise RuntimeError("kNN not fitted; call fit_clusters first.")
        distances, indices = self.kNN.kneighbors(candidate_vec.reshape(1, -1), n_neighbors=k)
        return indices[0]

    # 8. Job-Fit "Test Your Resume" Module
    def job_fit_score(self, jd_text: str, centroid_index: int) -> float:
        if self.profession_centroids is None:
            raise RuntimeError("Clusters not fitted; call fit_clusters first.")
        jd_vec = self.embedder.encode([jd_text])[0]
        centroid = self.profession_centroids[centroid_index]
        sim = cosine_similarity(jd_vec.reshape(1, -1), centroid.reshape(1, -1))[0][0]
        sim_norm = (sim + 1) / 2.0
        return float(100.0 * sim_norm)


def main():
    """Example wiring for training from unified_resume_dataset.csv.

    This is mainly for manual testing; main training is done via train_and_evaluate.py.
    """
    unified_path = "unified_resume_dataset.csv"
    df = pd.read_csv(unified_path)

    text_col = "resume_text"
    label_col = "category"

    texts = df[text_col].astype(str).tolist()
    labels = df[label_col]

    pipeline = ResumeMLPipeline()

    # Semantic features
    semantic_vecs = pipeline.encode_texts(texts)

    # Structured features
    structured_vecs = pipeline.build_structured_features(df)

    # Feature fusion
    final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)

    # Clustering
    pipeline.fit_clusters(final_vectors, labels=labels)

    print("Pipeline training completed. Profession centroids shape:", pipeline.profession_centroids.shape)


if __name__ == "__main__":
    main()
