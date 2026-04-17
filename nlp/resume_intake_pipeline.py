"""Resume intake NLP pipeline.

Implements the plan from `nlp_intake_and_synonym_normalization_combined.md`:
- File handling & text extraction (PDF/DOCX/DOC/TXT)
- Cleanup & normalization
- Section detection
- Skill extraction & synonym normalization (rules + SBERT + fuzzy)
- Structured feature extraction (experience, projects, certifications, education)
- SBERT embedding generation
- Final candidate_token dict for the ML model

External dependencies (install as needed):
    pip install pdfminer.six python-docx textract sentence-transformers rapidfuzz

Optional (if you extend PDF OCR support):
    pip install pymupdf pytesseract pillow
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from rapidfuzz import fuzz

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:  # pragma: no cover - handled at runtime
    pdfminer_extract_text = None  # type: ignore

try:
    import docx  # python-docx
except ImportError:  # pragma: no cover - handled at runtime
    docx = None  # type: ignore

try:
    import textract
except ImportError:  # pragma: no cover - handled at runtime
    textract = None  # type: ignore


logger = logging.getLogger(__name__)

SentenceTransformerType = None


def _get_sentence_transformer():
    """Lazily import SentenceTransformer to avoid heavy deps during test discovery."""
    global SentenceTransformerType
    if SentenceTransformerType is None:
        try:
            from sentence_transformers import SentenceTransformer as _SentenceTransformer
        except ImportError as exc:  # pragma: no cover - import-time dependency
            raise RuntimeError(
                "sentence-transformers is required for embedding/normalization. Install with `pip install sentence-transformers`."
            ) from exc
        SentenceTransformerType = _SentenceTransformer
    return SentenceTransformerType


# --------------------------------------------------------------------------------------
# 1. File type detection & text extraction
# --------------------------------------------------------------------------------------


def detect_file_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in {".docx"}:
        return "docx"
    if ext in {".doc"}:
        return "doc"
    if ext in {".txt"}:
        return "txt"
    raise ValueError(f"Unsupported file extension: {ext}")


def extract_text_from_pdf(path: Path) -> str:
    """Extract text from a PDF using pdfminer.

    If pdfminer is not installed, raises a clear error.
    """
    if pdfminer_extract_text is None:
        raise RuntimeError(
            "pdfminer.six is required for PDF extraction. Install with `pip install pdfminer.six`."
        )

    text = pdfminer_extract_text(str(path)) or ""
    return text


def extract_text_from_docx(path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    if docx is None:
        raise RuntimeError(
            "python-docx is required for DOCX extraction. Install with `pip install python-docx`."
        )

    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_text_from_doc(path: Path) -> str:
    """Extract text from legacy DOC using textract.

    This may require system dependencies depending on OS.
    """
    if textract is None:
        raise RuntimeError(
            "textract is required for DOC extraction. Install with `pip install textract`."
        )

    raw = textract.process(str(path))
    return raw.decode("utf-8", errors="ignore")


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_file(path: Path | str) -> str:
    """High-level text extraction entry point.

    Supports: PDF, DOCX, DOC, TXT.
    """
    path = Path(path)
    file_type = detect_file_type(path)

    if file_type == "pdf":
        return extract_text_from_pdf(path)
    if file_type == "docx":
        return extract_text_from_docx(path)
    if file_type == "doc":
        return extract_text_from_doc(path)
    if file_type == "txt":
        return extract_text_from_txt(path)

    raise ValueError(f"Unsupported file type: {file_type}")


# --------------------------------------------------------------------------------------
# 2. Cleanup & normalization
# --------------------------------------------------------------------------------------


WHITESPACE_RE = re.compile(r"\s+")
HTML_TAG_RE = re.compile(r"<[^>]+>")
UNICODE_BULLETS_RE = re.compile(r"[•●▪■◦]")

# Simple month mapping for date normalization
MONTHS = {
    "jan": "01",
    "january": "01",
    "feb": "02",
    "february": "02",
    "mar": "03",
    "march": "03",
    "apr": "04",
    "april": "04",
    "may": "05",
    "jun": "06",
    "june": "06",
    "jul": "07",
    "july": "07",
    "aug": "08",
    "august": "08",
    "sep": "09",
    "sept": "09",
    "september": "09",
    "oct": "10",
    "october": "10",
    "nov": "11",
    "november": "11",
    "dec": "12",
    "december": "12",
}

# e.g. "Jan 2020", "January 2020" etc.
MONTH_YEAR_RE = re.compile(
    r"\b(" + "|".join(MONTHS.keys()) + r")\s+(20\d{2}|19\d{2})\b",
    re.IGNORECASE,
)


def normalize_dates(text: str) -> str:
    """Normalize month-year patterns to MM/YYYY.

    Example: "Jan 2020" -> "01/2020".
    """

    def _repl(match: re.Match) -> str:
        month_raw = match.group(1).lower()
        year = match.group(2)
        month = MONTHS.get(month_raw, month_raw)
        return f"{month}/{year}"

    return MONTH_YEAR_RE.sub(_repl, text)


def clean_and_normalize_text(raw_text: str) -> str:
    """Apply basic cleaning & normalization.

    - Lowercase
    - Remove HTML tags
    - Replace Unicode bullets with '-'
    - Normalize whitespace
    - Normalize simple month-year dates
    """
    text = raw_text
    text = HTML_TAG_RE.sub(" ", text)
    text = UNICODE_BULLETS_RE.sub("-", text)
    text = text.replace("\r", "\n")
    text = normalize_dates(text)
    text = text.lower()

    # Normalize whitespace per line but keep line breaks so that heading-based
    # section detection continues to work as expected.
    normalized_lines: list[str] = []
    for line in text.split("\n"):
        line = WHITESPACE_RE.sub(" ", line).strip()
        if line:
            normalized_lines.append(line)
    return "\n".join(normalized_lines)


# --------------------------------------------------------------------------------------
# 3. Section detection
# --------------------------------------------------------------------------------------


SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "skills": re.compile(r"^\s*skills[\s:\-]*$", re.IGNORECASE),
    "experience": re.compile(r"^\s*(work )?experience[\s:\-]*$", re.IGNORECASE),
    "education": re.compile(r"^\s*education[\s:\-]*$", re.IGNORECASE),
    "projects": re.compile(r"^\s*projects?[\s:\-]*$", re.IGNORECASE),
    "certifications": re.compile(r"^\s*certifications?[\s:\-]*$", re.IGNORECASE),
    "summary": re.compile(r"^\s*(summary|profile|about me)[\s:\-]*$", re.IGNORECASE),
}


def detect_sections(text: str) -> Dict[str, str]:
    """Split resume text into sections using simple heading regexes."""
    lines = [ln.strip() for ln in text.split("\n")]

    current_section: Optional[str] = None
    sections: Dict[str, List[str]] = {}

    for line in lines:
        if not line:
            continue

        matched_section = None
        for name, pattern in SECTION_PATTERNS.items():
            if pattern.match(line):
                matched_section = name
                break

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
            continue

        if current_section is None:
            current_section = "other"
            sections.setdefault(current_section, [])

        sections[current_section].append(line)

    return {name: "\n".join(content) for name, content in sections.items()}


# --------------------------------------------------------------------------------------
# 4. Skill extraction
# --------------------------------------------------------------------------------------


def extract_skill_tokens_from_section(skills_text: str) -> List[str]:
    """Extract raw skill tokens from a skills section.

    Splits on commas, semicolons, and line breaks, trimming whitespace.
    """
    if not skills_text:
        return []

    raw_tokens = re.split(r"[,;\n]", skills_text)
    tokens = [tok.strip().lower() for tok in raw_tokens if tok.strip()]
    return tokens


def extract_skill_candidates(sections: Dict[str, str]) -> List[str]:
    """Gather potential skill tokens from sections.

    Currently focuses on the 'skills' section, but can be extended.
    """
    skills_text = sections.get("skills", "")
    return extract_skill_tokens_from_section(skills_text)


# --------------------------------------------------------------------------------------
# 5. Synonym normalization (rules + SBERT + fuzzy)
# --------------------------------------------------------------------------------------


DEFAULT_CANONICAL_SKILLS: List[str] = [
    # programming languages
    "python",
    "java",
    "c++",
    "javascript",
    "typescript",
    "sql",
    "c",
    "c#",
    # data & ml
    "machine learning",
    "deep learning",
    "data science",
    "nlp",
    "computer vision",
    # frameworks & tools
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "react",
    "node.js",
    "docker",
    "kubernetes",
    # cloud
    "aws",
    "azure",
    "gcp",
]


DEFAULT_RULES: Dict[str, str] = {
    # shortcuts / aliases
    "ml": "machine learning",
    "dl": "deep learning",
    "js": "javascript",
    "ts": "typescript",
    "react.js": "react",
    "nodejs": "node.js",
    "py": "python",
    "sklearn": "scikit-learn",
    "gcloud": "gcp",
}


@dataclass
class SynonymNormalizerConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.75
    fuzzy_threshold: float = 85.0


class SynonymNormalizer:
    """Normalize free-form skill tokens to canonical skills.

    Uses:
    - Rule-based mapping
    - SBERT semantic similarity
    - Fuzzy Levenshtein matching
    """

    def __init__(
        self,
        canonical_skills: Optional[List[str]] = None,
        rules: Optional[Dict[str, str]] = None,
        config: Optional[SynonymNormalizerConfig] = None,
    ) -> None:
        self.canonical_skills = canonical_skills or DEFAULT_CANONICAL_SKILLS
        self.rules = {k.lower(): v.lower() for k, v in (rules or DEFAULT_RULES).items()}
        self.config = config or SynonymNormalizerConfig()

        logger.info("Loading SBERT model %s", self.config.model_name)
        SentenceTransformer = _get_sentence_transformer()
        self.model = SentenceTransformer(self.config.model_name)
        self._canonical_embeddings = self._encode_skills(self.canonical_skills)

    def _encode_skills(self, skills: List[str]) -> np.ndarray:
        emb = self.model.encode(skills, convert_to_numpy=True, normalize_embeddings=True)
        return emb.astype("float32")

    def _encode_token(self, token: str) -> np.ndarray:
        emb = self.model.encode([token], convert_to_numpy=True, normalize_embeddings=True)
        return emb.astype("float32")[0]

    def _semantic_match(self, token: str) -> Optional[str]:
        if not token.strip():
            return None
        vec = self._encode_token(token)
        sims = np.dot(self._canonical_embeddings, vec)
        idx = int(sims.argmax())
        best_sim = float(sims[idx])
        if best_sim >= self.config.similarity_threshold:
            return self.canonical_skills[idx]
        return None

    def _fuzzy_match(self, token: str) -> Optional[str]:
        best_skill = None
        best_score = 0.0
        for canon in self.canonical_skills:
            score = float(fuzz.ratio(token, canon))
            if score > best_score:
                best_score = score
                best_skill = canon
        if best_skill and best_score >= self.config.fuzzy_threshold:
            return best_skill
        return None

    def normalize_token(self, token: str) -> Optional[str]:
        t = token.strip().lower()
        if not t:
            return None

        # 1) rule-based
        if t in self.rules:
            return self.rules[t]

        # 2) direct canonical match
        if t in self.canonical_skills:
            return t

        # 3) semantic match
        sem = self._semantic_match(t)
        if sem is not None:
            return sem

        # 4) fuzzy match
        fuzzy_match = self._fuzzy_match(t)
        if fuzzy_match is not None:
            return fuzzy_match

        return t  # fallback: keep as-is

    def normalize_tokens(self, tokens: List[str]) -> List[str]:
        normalized: List[str] = []
        for tok in tokens:
            norm = self.normalize_token(tok)
            if norm is not None and norm not in normalized:
                normalized.append(norm)
        return normalized


# --------------------------------------------------------------------------------------
# 6. Structured feature extraction
# --------------------------------------------------------------------------------------


@dataclass
class FeatureScalerConfig:
    max_experience_years: float = 20.0
    max_projects: float = 20.0
    max_certifications: float = 10.0


def _clamp(v: float, min_v: float, max_v: float) -> float:
    return max(min_v, min(max_v, v))


def compute_years_of_experience(text: str) -> float:
    """Estimate years of experience from year spans in the text.

    Very rough heuristic: find all 4-digit years and compute (max - min).
    """
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    current_year = datetime.now().year
    years = [y for y in years if 1950 <= y <= current_year]

    if len(years) < 2:
        return 0.0

    return float(max(years) - min(years))


def count_bullets(text: str) -> int:
    """Count bullet-like lines in a section."""
    if not text:
        return 0

    count = 0
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*")) or UNICODE_BULLETS_RE.search(stripped):
            count += 1
    return count


def infer_education_level(text: str) -> int:
    """Map education to ordinal scale.

    0 = unknown
    1 = diploma
    2 = bachelor
    3 = master
    4 = phd
    """
    t = text.lower()

    if re.search(r"phd|doctorate|doctoral", t):
        return 4
    if re.search(r"master|msc|m\.s\.|mtech|m\.tech|ms in", t):
        return 3
    if re.search(r"bachelor|bsc|b\.s\.|btech|b\.tech|be |b\.e\.", t):
        return 2
    if re.search(r"diploma", t):
        return 1
    return 0


def extract_structured_features(
    sections: Dict[str, str],
    scaler: Optional[FeatureScalerConfig] = None,
) -> Dict[str, float]:
    """Compute numeric features and apply simple MinMax-style scaling."""
    scaler = scaler or FeatureScalerConfig()

    exp_text = sections.get("experience", "") or sections.get("other", "")
    years = compute_years_of_experience(exp_text)
    years_norm = _clamp(years / scaler.max_experience_years, 0.0, 1.0)

    proj_text = sections.get("projects", "")
    projects_count = float(count_bullets(proj_text))
    projects_norm = _clamp(projects_count / scaler.max_projects, 0.0, 1.0)

    cert_text = sections.get("certifications", "")
    certs_count = float(count_bullets(cert_text))
    certs_norm = _clamp(certs_count / scaler.max_certifications, 0.0, 1.0)

    edu_text = sections.get("education", "")
    edu_level = float(infer_education_level(edu_text))

    return {
        "experience": years_norm,
        "projects": projects_norm,
        "certifications": certs_norm,
        "education": edu_level,
    }


# --------------------------------------------------------------------------------------
# 7. Embedding generation (SBERT)
# --------------------------------------------------------------------------------------


class ResumeEmbedder:
    """Wraps SBERT to produce a single embedding for the full resume text."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        SentenceTransformer = _get_sentence_transformer()
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> List[float]:
        vec = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vec.astype("float32").tolist()


# --------------------------------------------------------------------------------------
# 8. Orchestration: build final candidate token
# --------------------------------------------------------------------------------------


@dataclass
class ResumeIntakePipeline:
    normalizer: SynonymNormalizer
    embedder: ResumeEmbedder
    scaler_config: FeatureScalerConfig = field(default_factory=FeatureScalerConfig)

    @classmethod
    def with_defaults(cls) -> "ResumeIntakePipeline":
        normalizer = SynonymNormalizer()
        embedder = ResumeEmbedder()
        return cls(normalizer=normalizer, embedder=embedder)

    def process_file(self, path: Path | str) -> Dict:
        """Full pipeline from resume file to candidate_token dict."""
        path = Path(path)

        # 1) text extraction
        raw_text = extract_text_from_file(path)

        # 2) cleanup
        cleaned_text = clean_and_normalize_text(raw_text)

        # 3) section detection
        sections = detect_sections(cleaned_text)

        # 4) skill extraction + normalization
        raw_skills = extract_skill_candidates(sections)
        normalized_skills = self.normalizer.normalize_tokens(raw_skills)

        # 5) structured features
        features = extract_structured_features(sections, self.scaler_config)

        # 6) embedding
        embedding = self.embedder.encode(cleaned_text)

        # 7) summary text (optional: top of resume or explicit summary section)
        summary_text = sections.get("summary") or ""

        candidate_token = {
            "embedding": embedding,
            "skills": normalized_skills,
            "experience": features["experience"],
            "projects": features["projects"],
            "certifications": features["certifications"],
            "education": features["education"],
            "summary": summary_text,
            "raw_text": cleaned_text,
        }

        return candidate_token


__all__ = [
    "extract_text_from_file",
    "clean_and_normalize_text",
    "detect_sections",
    "extract_skill_candidates",
    "SynonymNormalizer",
    "SynonymNormalizerConfig",
    "FeatureScalerConfig",
    "extract_structured_features",
    "ResumeEmbedder",
    "ResumeIntakePipeline",
]
