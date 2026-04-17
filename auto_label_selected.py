import pandas as pd

STRUCTURED_PATH = "resume_shortlisting_dataset_v2.csv"


def main() -> None:
    """Add a synthetic `Selected` column based on a simple heuristic.

    Heuristic (can be tuned later):
    - Parse `Years of Experience` as float.
    - Count number of projects and certificates by splitting on commas.
    - Mark Selected = 1 if:
        * Years of Experience >= 5
      OR
        * Years of Experience >= 3 AND projects_count >= 3
      OR
        * certificates_count >= 3
      Else Selected = 0.

    This is only to enable weight learning; in a real system, you should
    replace this with actual historical selection labels.
    """

    df = pd.read_csv(STRUCTURED_PATH)

    # Parse years of experience
    years = pd.to_numeric(df["Years of Experience"], errors="coerce").fillna(0.0)

    def _count_items(series: pd.Series) -> pd.Series:
        return series.fillna("").astype(str).apply(
            lambda s: 0 if s.strip() == "" else len(s.split(","))
        )

    projects_count = _count_items(df["Projects"])
    certificates_count = _count_items(df["Certificates"])

    selected = (
        (years >= 5.0)
        | ((years >= 3.0) & (projects_count >= 3))
        | (certificates_count >= 3)
    ).astype(int)

    df["Selected"] = selected

    df.to_csv(STRUCTURED_PATH, index=False)
    print(
        "Added synthetic 'Selected' column to",
        STRUCTURED_PATH,
        "(1 = selected, 0 = not selected).",
    )
    print(
        "Counts:",
        selected.value_counts().to_dict(),
    )


if __name__ == "__main__":
    main()
