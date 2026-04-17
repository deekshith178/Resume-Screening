import pandas as pd
import numpy as np

print("=" * 60)
print("DATASET ANALYSIS REPORT")
print("=" * 60)

# 1. Analyze unified_resume_dataset.csv
print("\n1. unified_resume_dataset.csv")
print("-" * 60)
df1 = pd.read_csv('unified_resume_dataset.csv')
print(f"   Total rows: {len(df1)}")
print(f"   Columns: {list(df1.columns)}")
print(f"   Missing values:")
for col in df1.columns:
    missing = df1[col].isnull().sum()
    if missing > 0:
        print(f"     - {col}: {missing} ({missing/len(df1)*100:.1f}%)")

print(f"\n   Categories: {sorted(df1['category'].unique())}")
print(f"   Category distribution:")
for cat, count in df1['category'].value_counts().items():
    print(f"     - {cat}: {count}")

print(f"\n   Selected distribution:")
print(f"     - Selected (1): {df1['selected'].sum()}")
print(f"     - Not Selected (0): {(df1['selected'] == 0).sum()}")

print(f"\n   Numeric ranges:")
print(f"     - Years experience: {df1['years_experience'].min():.1f} - {df1['years_experience'].max():.1f}")
print(f"     - Projects count: {df1['projects_count'].min()} - {df1['projects_count'].max()}")
print(f"     - Certificates count: {df1['certificates_count'].min()} - {df1['certificates_count'].max()}")

# Check for potential issues
issues1 = []
if df1['years_experience'].min() < 0:
    issues1.append("Negative years of experience found")
if df1['projects_count'].min() < 0:
    issues1.append("Negative project count found")
if df1['certificates_count'].min() < 0:
    issues1.append("Negative certificate count found")
if len(df1['resume_text'].str.strip()) == 0:
    issues1.append("Empty resume text found")
if issues1:
    print(f"\n   WARNING: POTENTIAL ISSUES:")
    for issue in issues1:
        print(f"     - {issue}")
else:
    print(f"\n   OK: No obvious data quality issues detected")

# 2. Analyze resume_shortlisting_dataset_v2.csv
print("\n2. resume_shortlisting_dataset_v2.csv")
print("-" * 60)
df2 = pd.read_csv('resume_shortlisting_dataset_v2.csv')
print(f"   Total rows: {len(df2)}")
print(f"   Columns: {list(df2.columns)}")
print(f"   Missing values:")
for col in df2.columns:
    missing = df2[col].isnull().sum()
    if missing > 0:
        print(f"     - {col}: {missing} ({missing/len(df2)*100:.1f}%)")

if 'Selected' in df2.columns:
    print(f"\n   Selected distribution:")
    print(f"     - Selected (1): {df2['Selected'].sum()}")
    print(f"     - Not Selected (0): {(df2['Selected'] == 0).sum()}")
else:
    print(f"\n   ⚠️  'Selected' column NOT FOUND")

years_exp = pd.to_numeric(df2['Years of Experience'], errors='coerce')
print(f"\n   Numeric ranges:")
print(f"     - Years experience: {years_exp.min():.1f} - {years_exp.max():.1f}")

# Check for potential issues
issues2 = []
if 'Selected' not in df2.columns:
    issues2.append("Missing 'Selected' column (required for weight learning)")
else:
    print(f"   OK: 'Selected' column found")
empty_skills = (df2['Skills'].str.strip() == '').sum()
if empty_skills > 0:
    issues2.append(f"{empty_skills} rows with empty Skills")
empty_projects = (df2['Projects'].str.strip() == '').sum()
if empty_projects > 0:
    issues2.append(f"{empty_projects} rows with empty Projects")
empty_certs = (df2['Certificates'].str.strip() == '').sum()
if empty_certs > 0:
    issues2.append(f"{empty_certs} rows with empty Certificates")
if issues2:
    print(f"\n   WARNING: POTENTIAL ISSUES:")
    for issue in issues2:
        print(f"     - {issue}")
else:
    print(f"\n   OK: No obvious data quality issues detected")

# 3. Check alignment between datasets
print("\n3. Dataset Alignment Check")
print("-" * 60)
print(f"   unified_resume_dataset.csv rows: {len(df1)}")
print(f"   resume_shortlisting_dataset_v2.csv rows: {len(df2)}")
if len(df1) != len(df2):
    print(f"   WARNING: MISMATCH: Datasets have different row counts!")
    print(f"      This is handled by build_unified_dataset.py using min()")
else:
    print(f"   OK: Row counts match")

# 4. Check if UpdatedResumeDataSet_cleaned.csv exists
print("\n4. Source Dataset Check")
print("-" * 60)
try:
    df3 = pd.read_csv('UpdatedResumeDataSet_cleaned.csv', nrows=1)
    print(f"   OK: UpdatedResumeDataSet_cleaned.csv exists")
    print(f"   Columns: {list(df3.columns)}")
except FileNotFoundError:
    print(f"   WARNING: UpdatedResumeDataSet_cleaned.csv NOT FOUND")
    print(f"      This is required to build unified_resume_dataset.csv")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)

