# Combined Development Plan: NLP Intake Pipeline + Synonym Normalization System

This document merges the **NLP Intake Development Plan** and the **Synonym Normalization & Semantic Standardization Plan** into a single, complete, production-ready pipeline for resume ingestion.

It describes how resumes are:
1. Uploaded & sanitized
2. Parsed into text
3. Cleaned & normalized
4. Broken into sections
5. Mapped to canonical skill vocabulary (synonym normalization)
6. Converted into structured numeric features
7. Embedded using SBERT
8. Output as unified NLP tokens for the ML model

This combined plan ensures the system can handle:
- Similar words
- Abbreviations
- Typos
- Diverse resume formats (PDF/DOCX/TXT)
- Mixed skill expressions

---

# 1. Full NLP Architecture Overview

```
            Resume Files (PDF, DOCX, TXT)
                        ↓
     ┌───────────────────────────────────┐
     │ 1. File Handling & Security Scan │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │     2. Text Extraction Layer      │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │ 3. Cleanup & Normalization        │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │ 4. Section Detection              │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │ 5. Synonym Normalization Layer    │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │ 6. Feature Extraction (Numeric)   │
     └───────────────────────────────────┘
                        ↓
     ┌───────────────────────────────────┐
     │ 7. Semantic Embedding (SBERT)     │
     └───────────────────────────────────┘
                        ↓
     Final NLP Candidate Token
```

---

# 2. File Handling & Sanitization

### Supported Formats
- PDF
- DOCX
- DOC
- TXT

### Security Steps
- Virus scan with ClamAV
- Reject unsupported formats
- Reject password-protected PDFs
- Reject files > 10 MB
- Validate MIME types

---

# 3. Text Extraction Layer

### PDF
- `pdfminer.six` for digital PDFs
- `PyMuPDF` for layout-aware extraction
- Tesseract OCR fallback for scanned PDFs

### DOC / DOCX
- `python-docx` for DOCX
- `textract` / `antiword` for legacy DOC

### TXT
- Direct read with UTF-8 handling

---

# 4. Cleanup & Text Normalization

### Tasks
- Lowercase text
- Remove weird Unicode symbols
- Normalize whitespace
- Remove HTML tags (if any)
- Replace bullet characters with dots
- Standardize dates (e.g., "Jan 2020" → "01/2020")
- Optional lemmatization

---

# 5. Section Detection (Rule-Based NLP)

Use regex patterns to identify:
- Skills
- Experience
- Education
- Projects
- Certifications
- Summary

**Example Regex:**
```
skills[\s:\-]*
education[\s:\-]*
experience[\s:\-]*
```

Split resume into sections using these matches.

---

# 6. Synonym Normalization Layer (Key Component)

This ensures the machine understands similar words by converting them into **canonical skill forms**.

### 6.1 Rule-Based Dictionary Normalization
```
{"ml": "machine learning", "js": "javascript"}
{"react.js": "react", "py": "python"}
```

### 6.2 Embedding-Based Semantic Normalization
1. Create a canonical skill vocabulary (500–2000 skills)
2. Compute SBERT embedding for each
3. For each extracted token:
   - Compute cosine similarity with canonical skills

### Assignment Rule
\[
Normalized(t) = argmax(Sim(t, c_i))  \text{ if Sim >= 0.75 }
\]

### 6.3 Fuzzy Matching (Levenshtein)
Handles typos:
```
fuzzy_ratio(word, skill) ≥ 85
```

### Output
A clean set of canonical skills.

---

# 7. Structured Feature Extraction

Using structured info:
- Skills (normalized)
- Experience → extracted using year spans
- Projects → count bullet items under "Projects"
- Certifications → count entries
- Education → map to ordinal scale

### Example Education Scale
```
Diploma = 1
Bachelor = 2
Master = 3
PhD = 4
```

### Normalization
Use MinMax scaling:
\[
x' = \frac{x - x_{min}}{x_{max}-x_{min}}
\]

---

# 8. Semantic Embedding Generation (SBERT)

Use:
- Model: `all-MiniLM-L6-v2`
- Output: 384–768 dimensional vector

### Formula
```
resume_vector = SBERT.encode(cleaned_resume_text)
```

This encapsulates:
- Meaning
- Context
- Skill relationships

---

# 9. Final NLP Candidate Token Structure
```
candidate_token = {
  "embedding": resume_vector,
  "skills": normalized_skill_list,
  "experience": years_norm,
  "projects": projects_norm,
  "certifications": certs_norm,
  "education": edu_level,
  "summary": summary_text,
  "raw_text": cleaned_resume_text
}
```

This is passed to the ML Scoring Engine.

---

# 10. Integration With ML Pipeline

The ML model uses:
- Canonical skills → improve scoring accuracy
- Clean embeddings → stable cluster assignment
- Numeric fields → increase scoring fairness

The synonym normalization ensures:
- Better hybrid candidate detection
- Better similarity computations
- Better guidance recommendations

---

# 11. Evaluation Plan

### NLP Evaluation Metrics:
- Skill extraction accuracy
- Normalization confidence (avg similarity)
- Fuzzy correction success rate
- Section detection accuracy
- OCR fallback accuracy

### Test Plan
- Use 50–100 manually reviewed resumes
- Validate:
  - Correct section splits
  - Correct canonical skills
  - Clean embedding output

---

# 12. Future Enhancements
- Integrate LayoutLM for layout-aware extraction
- Use transformer-based NER for skills
- Build domain-specific synonym dictionaries
- Add multi-language resume support
- Expand canonical vocabulary via LLM-assisted clustering

---

# 13. Summary
This combined plan covers **every step required** to:
- Ingest resumes safely
- Extract & clean text
- Detect sections
- Normalize synonyms intelligently
- Build structured + semantic features
- Output consistent NLP tokens for ML ranking

It ensures the model understands similar/variant skill words and maintains high accuracy across diverse resume formats.

