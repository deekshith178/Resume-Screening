# Development Plan: Machine Learning Model for Resume Shortlisting System

This document explains **exactly how to build the ML model** that powers the Resume Shortlisting, Guidance, and Hybrid Candidate Detection features we discussed. It contains all formulas, steps, pipelines, and logic.

---

# 1. Overview of the ML Model
The ML component integrates **textual embeddings**, **structured features**, **clustering**, **distance-based scoring**, and **k-NN guidance** into one unified intelligent system.

The model pipeline consists of:
1. Resume Text Extraction
2. Text Embedding (SBERT)
3. Structured Feature Extraction
4. Feature Fusion
5. Clustering into Profession Zones
6. Scoring Engine (Weighted + Distance-based)
7. Hybrid Candidate Detection
8. Guidance Engine (k-NN)
9. Test-Fit Engine (JD → embedding → similarity)

---

# 2. Data Inputs
We use two datasets:
- **Dataset 1:** Resume text + category (`UpdatedResumeDataSet_cleaned.csv`)
- **Dataset 2:** Structured features (`skills`, `years_experience`, `projects`, `certificates`)

---

# 3. Step-by-Step Model Construction

## 3.1 Resume Text Embedding (Semantic Feature Extraction)
Use **Sentence-BERT (`all-MiniLM-L6-v2`)** to convert resume text into a 768‑dimensional vector.

**Formula:**
```
resume_vector = SBERT.encode(resume_text)
```

Benefits:
- Captures meaning, not just keywords.
- Understands synonyms ("ML Engineer" ~ "AI Developer").

---

## 3.2 Structured Feature Vectorization
Extract numeric representation from structured dataset.

### Features:
- Years of experience → `E_raw`
- Projects count → `P_raw`
- Certificates count → `C_raw`

### Normalization:
Use MinMax scaling:
\[
x' = \frac{x - x_{min}}{x_{max}-x_{min}}
\]

### Final Structured Vector:
```
[E_norm, P_norm, C_norm]
```
All values range from 0 to 1.

---

## 3.3 Feature Fusion
Concatenate semantic vector + structured vector:
```
final_vector = [resume_vector || structured_vector]
```
This forms the **candidate token**.

---

# 4. Clustering Model (Profession Zones)
Cluster candidates according to their feature vectors.

### Two recommended options:
**Option A: K-Means** (fixed number of professions)
```
kmeans = KMeans(n_clusters = number_of_categories)
clusters = kmeans.fit_predict(final_vectors)
```

**Option B: HDBSCAN** (automatically finds clusters)
```
hdbscan.HDBSCAN(min_cluster_size=15)
```

### Profession Centroids
For each profession:
```
centroid_profession = mean(final_vectors_in_cluster)
```
These centroids are used to compute similarity + scoring.

---

# 5. Scoring Engine
A candidate’s score is computed using:
1. **Skill similarity** (semantic)
2. **Experience level**
3. **Project involvement**
4. **Certificates**

The final score is in **0–100** range.

## 5.1 Skill Similarity (Semantic Matching)
Compute cosine similarity between candidate vector and profession centroid:
\[
S = \frac{v_{candidate} \cdot v_{centroid}}{||v_{candidate}|| \; ||v_{centroid}||}
\]
Normalize to 0–1:
\[
S_{norm} = \frac{S + 1}{2}
\]

---

## 5.2 Weighted Score Formula
Final score:
\[
Score = 100 \times (w_S S + w_E E + w_P P + w_C C)
\]

### Default Weights:
- Skills similarity = 0.50
- Experience = 0.25
- Projects = 0.15
- Certificates = 0.10

Weights can be tuned or learned.

---

## 5.3 Learning the Weights Automatically
Use logistic regression on historical `Selected` labels.

```
X = [S, E, P, C]
y = Selected
model = LogisticRegression()
model.fit(X, y)
```
Normalize coefficients:
```
w_i = coef_i / sum(|coef|)
```
These become new weights.

---

# 6. Hybrid Candidate Detection
Some candidates belong equally to two professions.
We detect them with a **confidence metric**.

### Step 1: Compute similarity to all profession centroids
```
similarities = cosine(candidate, centroid_i)
```

### Step 2: Sort and compare top 2
\[
Confidence = | sim_{top1} - sim_{top2} |
\]

### Step 3: Condition
- If `Confidence < 0.1` → **Hybrid Candidate**

### Step 4: Hybrid Centroid
\[
centroid_{hybrid} = \frac{centroid_{top1} + centroid_{top2}}{2}
\]
Use this centroid for scoring.

---

# 7. Guidance Model (k-NN Based)
Only triggered when candidate opts in OR recruiter enables guidance for unselected profiles.

### 7.1 Nearest Neighbor Search
```
kNN = NearestNeighbors(n_neighbors = 5)
neighbors = kNN.fit(final_vectors)
```

### 7.2 Skill Gap Detection
```
missing_skills = centroid_core_skills - candidate_skills
```
Rank missing skills by importance.

### 7.3 External API Suggestions (Optional)
For each missing skill:
- Coursera
- Udemy
- YouTube tutorial links
- Job role matches

---

# 8. Job-Fit “Test Your Resume” Module
Candidate enters:
- Job title
- Job description text
- Company name (optional)

### Step 1: Embed JD using SBERT
```
jd_vector = SBERT.encode(JD_text)
```

### Step 2: Compute similarity to profession centroids
Pick the nearest centroid.

### Step 3: Compute fit score using same scoring formula.

---

# 9. Visualization Layer
Use PCA or UMAP to reduce vectors to 2D.

Plot:
- Profession centroids (stars)
- Candidates (dots)
- Hybrid candidates (triangles)

Helps recruiters visually interpret clusters.

---

# 10. End-to-End ML Pipeline Summary

1. **Parse resumes** → extract text.
2. **Embed text** → SBERT vector.
3. **Extract structured data** → normalize.
4. **Fuse vectors** → candidate token.
5. **Cluster tokens** → profession zones.
6. **Compute centroid similarities** → semantic matching.
7. **Compute weighted score**.
8. **Detect hybrid candidates**.
9. **Generate guidance** (optional).
10. **Enable candidate test-fit**.

---

# 11. Model Evaluation
Evaluate using:
- ROC-AUC
- Precision@K
- Recall
- Score distribution
- Override frequency (feedback loop)

---

# 12. Future ML Enhancements
- Upgrade to OpenAI/Cohere embeddings.
- Skill ontology mapping (ESCO, O*NET).
- Reinforcement learning from recruiter overrides.
- Multi-language resume processing.
- Bias/fairness adjustment layers.

---

This plan provides everything needed to build the ML component of the Resume Shortlisting System exactly as we designed it in our full discussion.

