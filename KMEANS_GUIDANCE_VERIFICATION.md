# K-Means Guidance System Verification

## Summary of Changes

The guidance system has been enhanced to properly use **k-means clustering and k-NN** to provide personalized guidance to candidates based on similar successful candidates, as specified in the design document (`development_plan_ml_model.md`).

### What Was Fixed

**Before:** The guidance system only compared candidate skills against a hardcoded list of core skills per category.

**After:** The guidance system now:
1. Uses k-NN to find the k closest successful candidates in the same category
2. Extracts skills from those similar candidates
3. Identifies skills present in neighbors but missing from the candidate
4. Falls back to static method if ML pipeline is not available

### Files Modified

1. **`guidance_engine.py`**
   - Added `compute_missing_skills_kmeans()` method that uses k-NN
   - Enhanced `compute_missing_skills()` to try k-means first, then fallback
   - Added support for ML pipeline and training dataset
   - Added `neighbor_skills` and `method` fields to `GuidanceResult`

2. **`nlp/nlp_intake.py`**
   - Added `build_candidate_token_from_text()` method to build tokens from text directly (needed for processing neighbor resumes)

3. **`backend/main.py`**
   - Updated startup to load training dataset (`_TRAINING_DF`)
   - Updated all guidance endpoints to pass ML pipeline and training data to `GuidanceEngine`
   - All guidance endpoints now use k-means method by default

### How It Works

1. **Training Phase:**
   - ML pipeline clusters candidates using k-means
   - k-NN index is built on all training candidates
   - Training dataset is loaded with resume texts

2. **Guidance Generation:**
   - Candidate's resume is converted to feature vector (semantic + structured)
   - k-NN finds k=5 nearest neighbors in the vector space
   - Neighbors are filtered by:
     - Same category as target
     - Successful candidates (if 'selected' column exists)
   - Skills are extracted from neighbor resumes using NLP pipeline
   - Missing skills = skills in neighbors but not in candidate
   - Skills are ranked by frequency in neighbors

3. **Fallback:**
   - If k-means method fails or ML pipeline unavailable, falls back to static core skills list

### Verification Steps

#### 1. Check Backend Startup Logs
When starting the backend, you should see:
```
[startup] Loading training dataset...
[startup] Training dataset loaded: X rows
[startup] Loading ML pipeline...
[startup] Model loaded successfully. Categories: [...]
```

#### 2. Test Guidance Endpoint
Call the guidance endpoint and check the response:
```python
# The response should include:
{
    "missing_skills": [...],
    "suggested_resources": {...},
    "method": "kmeans"  # Should be "kmeans" not "static"
}
```

#### 3. Verify k-NN is Working
- Check that `pipeline.kNN` is not None after pipeline loads
- Check that guidance results have `method="kmeans"` when ML pipeline is available
- Check that `neighbor_skills` field is populated in results

#### 4. Manual Test
1. Start the backend server
2. Upload a resume for a candidate
3. Request guidance for a specific job category
4. Verify that:
   - Missing skills are identified
   - The method used is "kmeans" (not "static")
   - Skills are relevant to the category and similar successful candidates

### Expected Behavior

**When ML pipeline is available:**
- Guidance uses k-NN to find similar successful candidates
- Missing skills are derived from actual successful candidates, not just hardcoded lists
- More personalized and data-driven recommendations

**When ML pipeline is NOT available:**
- Falls back to static core skills list
- Still provides guidance, but less personalized

### Key Implementation Details

1. **k-NN Integration:**
   - Uses `pipeline.nearest_neighbors()` which was already implemented in `ml_pipeline.py`
   - Returns indices into the training dataset
   - Indices are used to access corresponding resume texts

2. **Skill Extraction:**
   - For each neighbor, resume text is processed through NLP pipeline
   - Skills are extracted and normalized
   - Skills are counted and ranked by frequency

3. **Category Filtering:**
   - Only neighbors in the same category are considered
   - Optionally filters by success (selected=1) if that column exists

4. **Error Handling:**
   - Gracefully falls back to static method if k-means fails
   - Handles missing data, parsing errors, etc.

### Testing

Run the test script:
```bash
python test_kmeans_guidance.py
```

This will:
- Load the training dataset
- Load/initialize the ML pipeline
- Create a test candidate
- Generate guidance using k-means
- Verify the method used is "kmeans"
- Compare with static method

### Troubleshooting

**If guidance always uses "static" method:**
1. Check that `_FILE_PIPELINE` is not None in backend
2. Check that `_TRAINING_DF` is not None in backend
3. Check that `pipeline.kNN` is not None
4. Check backend logs for errors during guidance generation

**If k-NN returns wrong neighbors:**
1. Verify training dataset indices match k-NN indices
2. Check that `fit_clusters()` was called with the same data
3. Verify category filtering is working correctly

### Next Steps

1. Monitor guidance quality in production
2. Consider adding metrics to track:
   - Percentage of guidance using k-means vs static
   - Quality of recommendations (user feedback)
   - Time taken for k-means guidance
3. Optimize skill extraction for better performance
4. Consider caching neighbor skills for common categories






