import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


# --- Data structures -----------------------------------------------------------------


@dataclass
class CandidateToken:
    """Unified NLP token for a single resume, ready for the ML model.

    This follows the structure in nlp_intake_and_synonym_normalization_combined.md.
    """

    embedding: np.ndarray
    skills: List[str]
    experience: float
    projects: float
    certifications: float
    education: int
    summary: str
    raw_text: str
    name: Optional[str] = None
    email: Optional[str] = None


# --- Helper functions ----------------------------------------------------------------


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def _standardize_bullets(text: str) -> str:
    # Replace common bullet characters with a dot so they are consistent
    return re.sub(r"[\u2022\u2023\u25E6\u2043\u2219]", " . ", text)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


# Very simple date normalization placeholder (e.g. "Jan 2020" -> "01/2020")
MONTH_MAP = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}


def _standardize_dates(text: str) -> str:
    def repl(match: re.Match) -> str:
        month = MONTH_MAP.get(match.group(1).lower(), "01")
        year = match.group(2)
        return f"{month}/{year}"

    # Patterns like "Jan 2020", "JAN, 2019" etc.
    return re.sub(r"\b([A-Za-z]{3})[ ,]+(20\d{2})\b", repl, text)


# --- Section detection ---------------------------------------------------------------


SECTION_PATTERNS = {
    "skills": re.compile(r"\bskills[\s:\-]*", re.IGNORECASE),
    "experience": re.compile(r"\bexperience[\s:\-]*", re.IGNORECASE),
    "education": re.compile(r"\beducation[\s:\-]*", re.IGNORECASE),
    "projects": re.compile(r"\bprojects?[\s:\-]*", re.IGNORECASE),
    "certifications": re.compile(r"\b(certifications?|certs?)[\s:\-]*", re.IGNORECASE),
    "summary": re.compile(r"\b(summary|profile|about me)[\s:\-]*", re.IGNORECASE),
}


def _detect_sections(text: str) -> Dict[str, str]:
    """Split resume into sections using simple regex-based headers.

    Returns a dict: section_name -> section_text
    """

    lower = text.lower()
    indices = []
    for name, pattern in SECTION_PATTERNS.items():
        for m in pattern.finditer(lower):
            indices.append((m.start(), name))

    if not indices:
        return {"full": text}

    indices.sort()
    sections: Dict[str, str] = {}
    for i, (start, name) in enumerate(indices):
        end = indices[i + 1][0] if i + 1 < len(indices) else len(text)
        sections[name] = text[start:end].strip()

    return sections


# --- Synonym normalization -----------------------------------------------------------


# Minimal example dictionary; extend as needed
SKILL_SYNONYMS = {
    "ml": "machine learning",
    "machine-learning": "machine learning",
    "ai": "artificial intelligence",
    "js": "javascript",
    "react.js": "react",
    "py": "python",
    "c++": "cpp",
    "nlp": "natural language processing",
}

CANONICAL_SKILLS = sorted(set(SKILL_SYNONYMS.values()) | {
    "python",
    "javascript",
    "react",
    "java",
    "machine learning",
    "deep learning",
    "data analysis",
    "sql",
    "natural language processing",
})


class SkillNormalizer:
    """Combines rule-based and embedding-based skill normalization."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.embedder = SentenceTransformer(model_name)
        self.canonical_skills = CANONICAL_SKILLS
        # Pre-compute embeddings for canonical skills
        self.canonical_embs = self.embedder.encode(self.canonical_skills, show_progress_bar=False)

    def normalize_token(self, token: str, sim_threshold: float = 0.75) -> Optional[str]:
        """Normalize a single skill token.

        1. Apply dictionary mapping.
        2. Use SBERT similarity to map to nearest canonical skill.
        """

        t = token.strip().lower()
        if not t:
            return None

        # Rule-based dictionary
        if t in SKILL_SYNONYMS:
            return SKILL_SYNONYMS[t]

        # Embedding-based semantic normalization
        emb = self.embedder.encode([t], show_progress_bar=False)[0]
        sims = np.dot(self.canonical_embs, emb) / (
            np.linalg.norm(self.canonical_embs, axis=1) * np.linalg.norm(emb) + 1e-8
        )
        best_idx = int(np.argmax(sims))
        best_sim = float(sims[best_idx])
        if best_sim >= sim_threshold:
            return self.canonical_skills[best_idx]
        return None

    def normalize_list(self, tokens: List[str], sim_threshold: float = 0.75) -> List[str]:
        out: List[str] = []
        for t in tokens:
            norm = self.normalize_token(t, sim_threshold=sim_threshold)
            if norm is not None:
                out.append(norm)
        # Deduplicate while preserving order
        seen = set()
        unique: List[str] = []
        for s in out:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique


# --- Education mapping ---------------------------------------------------------------


EDU_LEVELS = {
    "diploma": 1,
    "bachelor": 2,
    "bsc": 2,
    "b.e": 2,
    "btech": 2,
    "master": 3,
    "msc": 3,
    "m.e": 3,
    "mtech": 3,
    "phd": 4,
    "doctorate": 4,
}


def _infer_education_level(text: str) -> int:
    lower = text.lower()
    for key, level in EDU_LEVELS.items():
        if key in lower:
            return level
    return 0  # unknown / not found


# --- NLP Intake Pipeline -------------------------------------------------------------


class NLPIntakePipeline:
    """End-to-end NLP intake pipeline to produce CandidateToken objects."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self.embedder = SentenceTransformer(model_name)
        self.skill_normalizer = SkillNormalizer(model_name=model_name)

    # 1–3: File reading + cleanup -----------------------------------------------------

    def read_file(self, path: str | Path) -> str:
        """Text loading for multiple resume formats.

        Supported:
        - .txt  → plain UTF-8 text
        - .pdf  → via PyMuPDF (fitz) if available, else pdfminer.six
        - .docx → via python-docx
        - .doc  → via textract if available

        If a required dependency is missing, a clear RuntimeError is raised.
        """

        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)

        suffix = p.suffix.lower()
        if suffix in {".txt", ""}:
            return p.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            return self._extract_pdf(p)
        if suffix == ".docx":
            return self._extract_docx(p)
        if suffix == ".doc":
            return self._extract_doc(p)

        raise RuntimeError(f"Unsupported file type: {suffix}")

    # --- Format-specific extractors ---------------------------------------------------

    def _extract_pdf(self, path: Path) -> str:
        """Extract text from a PDF file using PyMuPDF or pdfminer.six.

        Tries PyMuPDF (fitz) first for better layout; falls back to pdfminer.six.
        """

        try:
            import fitz  # type: ignore

            text_parts: list[str] = []
            with fitz.open(path) as doc:
                for page in doc:
                    text_parts.append(page.get_text())
            return "\n".join(text_parts)
        except Exception:
            # Fallback to pdfminer.six
            try:
                from pdfminer.high_level import extract_text  # type: ignore

                return extract_text(str(path))
            except Exception as e:
                raise RuntimeError(
                    "Cannot extract text from PDF. Install PyMuPDF (fitz) or pdfminer.six."
                ) from e

    def _extract_docx(self, path: Path) -> str:
        """Extract text from a DOCX file using python-docx."""

        try:
            from docx import Document  # type: ignore
        except Exception as e:
            raise RuntimeError("python-docx is required to read .docx files.") from e

        doc = Document(str(path))
        lines: list[str] = []
        for para in doc.paragraphs:
            if para.text:
                lines.append(para.text)
        return "\n".join(lines)

    def _extract_doc(self, path: Path) -> str:
        """Extract text from legacy .doc files using textract if available."""

        try:
            import textract  # type: ignore
        except Exception as e:
            raise RuntimeError("textract is required to read .doc files.") from e

        data = textract.process(str(path))
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return data.decode("latin1", errors="ignore")

    def clean_text(self, raw: str) -> str:
        text = raw
        text = _strip_html(text)
        text = _normalize_unicode(text)
        text = _standardize_bullets(text)
        text = _standardize_dates(text)
        text = text.lower()
        text = _normalize_whitespace(text)
        return text

    # 4: Section detection ------------------------------------------------------------

    def detect_sections(self, cleaned_text: str) -> Dict[str, str]:
        return _detect_sections(cleaned_text)

    # 5–7: Skill normalization & structured features ---------------------------------

    def extract_raw_skills(self, sections: Dict[str, str]) -> List[str]:
        """Extract raw skills from sections, with improved parsing."""
        # First try the skills section
        skill_text = sections.get("skills", "")
        
        # If no dedicated skills section, try to extract from summary or full text
        if not skill_text or len(skill_text.strip()) < 10:
            # Look for skills in summary section
            skill_text = sections.get("summary", "")
            if not skill_text or len(skill_text.strip()) < 10:
                # Fallback to full text, but only first 2000 chars to avoid noise
                full_text = sections.get("full", "")
                skill_text = full_text[:2000] if full_text else ""
        
        # Split on commas, semicolons, newlines, pipes, and bullets
        tokens = re.split(r"[\n,;/|•\-\*]", skill_text)
        
        # Clean and filter tokens
        cleaned_tokens = []
        for t in tokens:
            t = t.strip()
            # Filter out very short tokens, numbers, and common non-skill words
            if (len(t) >= 2 and 
                not t.isdigit() and 
                not re.match(r'^\d+$', t) and
                t.lower() not in ['and', 'or', 'the', 'a', 'an', 'with', 'using', 'via', 'etc']):
                cleaned_tokens.append(t)
        
        return cleaned_tokens

    def infer_years_experience(self, text: str) -> float:
        # Very simple heuristic: count patterns like "X years" or "X+ years"
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*years", text)
        years = [float(m) for m in matches]
        if years:
            return float(max(years))
        return 0.0

    def count_projects(self, sections: Dict[str, str]) -> int:
        proj_text = sections.get("projects", "")
        # Count bullet-like lines
        lines = proj_text.splitlines()
        count = 0
        for line in lines:
            if re.search(r"^\s*[\-*•]", line):
                count += 1
        return count

    def count_certifications(self, sections: Dict[str, str]) -> int:
        cert_text = sections.get("certifications", "")
        # Roughly count comma/newline separated entries
        tokens = re.split(r"[\n,;/]", cert_text)
        return sum(1 for t in tokens if t.strip())

    def infer_summary(self, sections: Dict[str, str]) -> str:
        if "summary" in sections:
            return sections["summary"].strip()
        # Fallback: first 3 lines of full text
        full = sections.get("full") or ""
        lines = full.splitlines()
        return " ".join(l.strip() for l in lines[:3])

    def extract_email(self, text: str) -> Optional[str]:
        # Simple email regex
        match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        return match.group(0) if match else None

    def infer_name(self, text: str, email: Optional[str]) -> Optional[str]:
        """Improved name extraction with multiple strategies."""
        # Use original text (not cleaned/lowercased) for name extraction
        original_lines = [l.strip() for l in text.splitlines() if l.strip()]
        
        # 1. Look for explicit "Name:" prefix (case-insensitive)
        name_prefix_regex = re.compile(r"^(?:name|candidate name|full name|applicant name)\s*[:\-]\s*(.*)", re.IGNORECASE)
        for line in original_lines[:25]:
            match = name_prefix_regex.match(line)
            if match:
                potential_name = match.group(1).strip()
                # Remove common suffixes like "Email:", "Phone:" if they appear
                potential_name = re.split(r'\s*(?:email|phone|mobile|address)', potential_name, flags=re.IGNORECASE)[0].strip()
                words = potential_name.split()
                if 1 <= len(words) <= 6:
                    return potential_name

        # 2. Extract name from email if available (before @ symbol)
        if email:
            email_name = email.split('@')[0]
            # Clean up common patterns: john.doe -> John Doe, john_doe -> John Doe
            email_name = email_name.replace('.', ' ').replace('_', ' ').replace('-', ' ')
            words = email_name.split()
            if 2 <= len(words) <= 4:
                # Capitalize properly
                formatted = ' '.join(w.capitalize() for w in words)
                return formatted

        # 3. Heuristic scan of top lines (use original case)
        ignore_terms = {
            "resume", "curriculum", "vitae", "cv", "page", "phone", "email", 
            "mobile", "address", "summary", "profile", "objective", "experience",
            "education", "skills", "projects", "contact", "links", "linkedin", "github",
            "portfolio", "website", "github.com", "linkedin.com"
        }
        
        for line in original_lines[:25]:  # Scan top 25 lines
            # Skip if it contains the email
            if email and email.lower() in line.lower():
                continue
            
            # Skip likely header/garbage lines
            lower_line = line.lower()
            if any(term in lower_line for term in ignore_terms):
                continue
                
            # Skip lines with phone numbers (multiple digits)
            if re.search(r"\d{3,}", line):
                continue
                
            # Skip lines with URLs
            if "http" in lower_line or "www." in lower_line or ".com" in lower_line:
                continue
            
            # Skip lines that are all lowercase (likely not a name header)
            if line.islower() and len(line) > 20:
                continue

            words = line.split()
            
            # Constraint: 2 to 6 words (e.g. "John Doe" to "Dr. Martin Luther King Jr.")
            if 2 <= len(words) <= 6:
                # Check if it looks like a name:
                # - Title case (John Doe)
                # - All caps (JOHN DOE) 
                # - Mixed case with first letter of each word capitalized
                is_title_case = all(w[0].isupper() for w in words if len(w) > 0 and w[0].isalpha())
                is_all_caps = line.isupper() and len(line) < 50
                
                if is_title_case or is_all_caps:
                    # Additional check: at least one word should be > 2 chars
                    if any(len(w) > 2 for w in words):
                        # Clean up any trailing punctuation
                        cleaned_name = re.sub(r"[,\.\-\|:;]+$", "", line).strip()
                        # Remove common prefixes
                        cleaned_name = re.sub(r"^(mr|mrs|ms|dr|prof)\.?\s+", "", cleaned_name, flags=re.IGNORECASE)
                        return cleaned_name.strip()
                    
        return None

    def build_candidate_token_from_text(self, text: str) -> CandidateToken:
        """Build a candidate token directly from text (without reading from file)."""
        # Store original text for name extraction (needs original case)
        original_text = text
        
        # 1–3) Clean text
        cleaned = self.clean_text(text)

        # 4) Detect sections (use cleaned for section detection)
        sections = self.detect_sections(cleaned)

        # 5) Extract and normalize skills
        raw_skills = self.extract_raw_skills(sections)
        normalized_skills = self.skill_normalizer.normalize_list(raw_skills)

        # 6) Structured features
        full_text = sections.get("full", cleaned)
        years_exp = self.infer_years_experience(full_text)
        projects = float(self.count_projects(sections))
        certs = float(self.count_certifications(sections))
        edu_level = _infer_education_level(cleaned)
        summary = self.infer_summary(sections)

        # 7) PII Extraction (use original text for name, cleaned for email)
        email = self.extract_email(original_text)  # Email regex works on original
        name = self.infer_name(original_text, email)  # Name needs original case

        # 8) SBERT embedding
        emb = self.embedder.encode([cleaned], show_progress_bar=False)[0]

        return CandidateToken(
            embedding=np.asarray(emb, dtype=np.float32),
            skills=normalized_skills,
            experience=float(years_exp),
            projects=projects,
            certifications=certs,
            education=edu_level,
            summary=summary,
            raw_text=cleaned,
            name=name,
            email=email,
        )

    def build_candidate_token(self, path: str | Path) -> CandidateToken:
        # 1–3) Read file (preserve original text for name extraction)
        raw_text = self.read_file(path)
        return self.build_candidate_token_from_text(raw_text)


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="NLP intake pipeline: convert resume files into candidate tokens.",
    )
    parser.add_argument("path", type=str, help="Path to resume file (e.g., .txt, .pdf, .docx)")
    args = parser.parse_args()

    pipeline = NLPIntakePipeline()
    token = pipeline.build_candidate_token(args.path)

    # For CLI inspection, print a JSON-friendly summary (embedding truncated)
    output = {
        "skills": token.skills,
        "experience": token.experience,
        "projects": token.projects,
        "certifications": token.certifications,
        "education": token.education,
        "summary": token.summary,
        "embedding_dim": int(token.embedding.shape[0]),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
