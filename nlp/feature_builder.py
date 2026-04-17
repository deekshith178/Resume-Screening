"""Feature builder for candidate_token.

This module converts the structured output of ResumeIntakePipeline
(candidate_token) into a single numeric feature vector suitable for
use with scikit-learn models or other ML frameworks.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

# Stable ordering of skills for multi-hot encoding.
# Adjust this list to match your domain / tech stack.
SKILL_VOCAB: List[str] = [
    "python",
    "java",
    "javascript",
    "machine learning",
    "deep learning",
    "data science",
    "nlp",
    "react",
    "docker",
    "aws",
]


def build_feature_vector(candidate_token: Dict) -> np.ndarray:
    """Convert candidate_token into a 1D numeric feature vector.

    Structure:
    [ SBERT embedding ... , experience, projects, certifications, education, skill_multi_hot ... ]
    """
    emb = np.asarray(candidate_token["embedding"], dtype="float32")

    numeric = np.asarray(
      [
        float(candidate_token.get("experience", 0.0)),
        float(candidate_token.get("projects", 0.0)),
        float(candidate_token.get("certifications", 0.0)),
        float(candidate_token.get("education", 0.0)),
      ],
      dtype="float32",
    )

    skills = set([s.lower() for s in candidate_token.get("skills", [])])
    skill_vec = np.asarray(
        [1.0 if skill in skills else 0.0 for skill in SKILL_VOCAB], dtype="float32"
    )

    return np.concatenate([emb, numeric, skill_vec], axis=0)
