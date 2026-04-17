import pandas as pd
from pathlib import Path


RESUME_TEXT_PATH = "UpdatedResumeDataSet_cleaned.csv"
STRUCTURED_PATH = "resume_shortlisting_dataset_v2.csv"
UNIFIED_PATH = "unified_resume_dataset.csv"


def _count_items(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).apply(
        lambda s: 0 if s.strip() == "" else len(s.split(","))
    )


def main() -> None:
    resumes_path = Path(RESUME_TEXT_PATH)
    structured_path = Path(STRUCTURED_PATH)

    if not resumes_path.exists():
        raise FileNotFoundError(resumes_path)
    if not structured_path.exists():
        raise FileNotFoundError(structured_path)

    resumes_df = pd.read_csv(resumes_path)
    structured_df = pd.read_csv(structured_path)

    # Align by minimum length (prototype assumption: first N rows correspond)
    n = min(len(resumes_df), len(structured_df))
    resumes_df = resumes_df.iloc[:n].reset_index(drop=True)
    structured_df = structured_df.iloc[:n].reset_index(drop=True)

    # Extract text + category
    text_col = "Resume" if "Resume" in resumes_df.columns else resumes_df.columns[1]
    label_col = "Category" if "Category" in resumes_df.columns else resumes_df.columns[0]

    resume_text = resumes_df[text_col].astype(str)
    category = resumes_df[label_col].astype(str)

    # Structured features
    years = pd.to_numeric(structured_df["Years of Experience"], errors="coerce").fillna(0.0)
    projects_count = _count_items(structured_df["Projects"]).astype(int)
    certificates_count = _count_items(structured_df["Certificates"]).astype(int)

    # Selected label: use existing column if present, else default to 0
    if "Selected" in structured_df.columns:
        selected = structured_df["Selected"].fillna(0).astype(int)
    else:
        selected = pd.Series(0, index=structured_df.index, dtype=int)

    unified = pd.DataFrame(
        {
            "resume_id": range(1, n + 1),
            "category": category,
            "resume_text": resume_text,
            "years_experience": years.astype(float),
            "projects_count": projects_count.astype(int),
            "certificates_count": certificates_count.astype(int),
            "selected": selected,
        }
    )

    unified.to_csv(UNIFIED_PATH, index=False)
    print(f"Wrote unified dataset with {len(unified)} rows to {UNIFIED_PATH}")


if __name__ == "__main__":
    main()
