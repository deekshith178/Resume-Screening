"""Test script to verify k-means based guidance is working correctly."""

import pandas as pd
import numpy as np
from pathlib import Path
from ml_pipeline import ResumeMLPipeline
from guidance_engine import GuidanceEngine
from nlp.nlp_intake import NLPIntakePipeline

def test_kmeans_guidance():
    """Test that k-means guidance properly identifies skills from similar candidates."""
    
    print("=" * 60)
    print("Testing k-means based guidance system")
    print("=" * 60)
    
    # 1. Load training dataset
    unified_path = Path("unified_resume_dataset.csv")
    if not unified_path.exists():
        print(f"ERROR: Training dataset not found at {unified_path}")
        return False
    
    print(f"\n1. Loading training dataset from {unified_path}...")
    training_df = pd.read_csv(str(unified_path))
    print(f"   Loaded {len(training_df)} candidates")
    print(f"   Categories: {sorted(training_df['category'].unique())}")
    
    # 2. Train/load ML pipeline
    print("\n2. Loading/initializing ML pipeline...")
    model_path = Path("trained_pipeline.joblib")
    
    if model_path.exists():
        print(f"   Loading existing model from {model_path}...")
        import joblib
        pipeline, categories = joblib.load(str(model_path))
    else:
        print("   Training new pipeline (this may take a minute)...")
        from score_resume_file import train_pipeline
        pipeline, categories = train_pipeline()
        import joblib
        joblib.dump((pipeline, categories), str(model_path))
        print("   Training complete!")
    
    print(f"   Pipeline loaded with {len(categories)} categories: {categories}")
    
    # 3. Verify k-NN is fitted
    if pipeline.kNN is None:
        print("   ERROR: k-NN not fitted in pipeline. Re-fitting...")
        # Re-fit clusters to ensure k-NN is available
        texts = training_df["resume_text"].astype(str).tolist()
        semantic_vecs = pipeline.encode_texts(texts)
        structured_vecs = pipeline.build_structured_features(training_df)
        final_vectors = pipeline.fuse_features(semantic_vecs, structured_vecs)
        pipeline.fit_clusters(final_vectors, labels=training_df["category"])
        print("   k-NN fitted successfully!")
    else:
        print("   ✓ k-NN is fitted and ready")
    
    # 4. Create a test candidate (lower-scoring candidate)
    print("\n3. Creating test candidate...")
    nlp_pipeline = NLPIntakePipeline()
    
    # Use a sample resume or create a minimal one
    test_resume_text = """
    John Doe
    Email: john.doe@example.com
    
    SUMMARY
    Recent graduate with basic Python knowledge and some data analysis experience.
    
    SKILLS
    Python, Excel, Basic Statistics
    
    EXPERIENCE
    1 year of internship experience in data entry
    
    PROJECTS
    1 small data analysis project
    
    CERTIFICATIONS
    None
    """
    
    # Save to temp file
    test_file = Path("test_candidate_resume.txt")
    test_file.write_text(test_resume_text)
    
    try:
        candidate_token = nlp_pipeline.build_candidate_token(str(test_file))
        print(f"   Candidate skills: {candidate_token.skills[:10]}")
        print(f"   Experience: {candidate_token.experience} years")
    finally:
        if test_file.exists():
            test_file.unlink()
    
    # 5. Test guidance with k-means
    print("\n4. Testing k-means guidance for 'Data Science' category...")
    ge = GuidanceEngine(
        ml_pipeline=pipeline,
        training_df=training_df,
    )
    
    try:
        result = ge.generate_guidance(
            candidate_token,
            category="Data Science",
            top_n=10,
            use_kmeans=True
        )
        
        print(f"\n   Guidance Method Used: {result.method}")
        print(f"   Missing Skills Found: {len(result.missing_skills)}")
        
        if result.method == "kmeans":
            print("   ✓ SUCCESS: k-means guidance is working!")
            print(f"\n   Missing skills identified from similar candidates:")
            for i, skill in enumerate(result.missing_skills[:10], 1):
                print(f"      {i}. {skill}")
            
            if result.neighbor_skills:
                print(f"\n   Skills found in nearest neighbors: {len(result.neighbor_skills)}")
                print(f"   Sample: {result.neighbor_skills[:5]}")
        else:
            print("   ⚠ WARNING: Fell back to static method (k-means not available)")
            print(f"   Missing skills from static list:")
            for i, skill in enumerate(result.missing_skills[:10], 1):
                print(f"      {i}. {skill}")
        
        # 6. Test guidance with static method (for comparison)
        print("\n5. Testing static guidance (for comparison)...")
        result_static = ge.generate_guidance(
            candidate_token,
            category="Data Science",
            top_n=10,
            use_kmeans=False
        )
        print(f"   Static method found {len(result_static.missing_skills)} missing skills")
        
        return result.method == "kmeans"
        
    except Exception as e:
        print(f"\n   ✗ ERROR: k-means guidance failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kmeans_guidance()
    print("\n" + "=" * 60)
    if success:
        print("✓ TEST PASSED: k-means guidance is working correctly!")
    else:
        print("✗ TEST FAILED: k-means guidance needs attention")
    print("=" * 60)






