"""Run guidance engine with progress indicators for SERP API calls."""

import sys
import os
import time
import numpy as np
from pathlib import Path

sys.stdout.write("Starting Guidance Engine Test for Data Science...\n")
sys.stdout.flush()

# Load .env
env_path = Path(".env")
if env_path.exists():
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from guidance_engine import GuidanceEngine
from nlp.nlp_intake import CandidateToken

# Create candidate
candidate = CandidateToken(
    embedding=np.zeros(384, dtype=np.float32),
    skills=["python"],
    experience=1.0,
    projects=2.0,
    certifications=0.0,
    education=2,
    summary="Python developer",
    raw_text="Python developer"
)

# Initialize with SERP API
serpapi_key = os.getenv("SERPAPI_KEY")
ge = GuidanceEngine(serpapi_key=serpapi_key, use_serpapi=True)

sys.stdout.write(f"\n{'='*70}\n")
sys.stdout.write("GUIDANCE ENGINE - DATA SCIENCE COURSES\n")
sys.stdout.write(f"{'='*70}\n\n")
sys.stdout.write(f"Mode: {'SERP API (Real-time results)' if ge.use_serpapi else 'Fallback URLs'}\n")
sys.stdout.write(f"API Key: {'✓ Loaded' if serpapi_key else '✗ Not found'}\n\n")
sys.stdout.flush()

# Compute missing skills first
sys.stdout.write("Step 1: Computing missing skills...\n")
sys.stdout.flush()
missing_skills = ge.compute_missing_skills(candidate, "Data Science", top_n=5)

sys.stdout.write(f"✓ Found {len(missing_skills)} missing skills\n\n")
sys.stdout.write("Missing Skills:\n")
for i, skill in enumerate(missing_skills, 1):
    sys.stdout.write(f"  {i}. {skill}\n")
sys.stdout.write("\n")
sys.stdout.flush()

# Get resources for each skill with progress
sys.stdout.write("Step 2: Fetching course resources (this may take 30-60 seconds)...\n")
sys.stdout.write("="*70 + "\n")
sys.stdout.flush()

resources_dict = {}
total_skills = len(missing_skills)

for idx, skill in enumerate(missing_skills, 1):
    sys.stdout.write(f"\n[{idx}/{total_skills}] Fetching resources for: {skill.upper()}\n")
    sys.stdout.write("  ⏳ Calling SERP API...\n")
    sys.stdout.flush()
    
    start_time = time.time()
    try:
        skill_resources = ge._suggest_resources_for_skill(skill, max_results=5)
        elapsed = time.time() - start_time
        
        resources_dict[skill] = skill_resources
        sys.stdout.write(f"  ✓ Found {len(skill_resources)} resources ({elapsed:.1f}s)\n")
        for i, url in enumerate(skill_resources[:3], 1):  # Show first 3
            sys.stdout.write(f"     {i}. {url[:70]}...\n" if len(url) > 70 else f"     {i}. {url}\n")
        if len(skill_resources) > 3:
            sys.stdout.write(f"     ... and {len(skill_resources) - 3} more\n")
        sys.stdout.flush()
    except Exception as e:
        sys.stdout.write(f"  ✗ Error: {e}\n")
        sys.stdout.flush()

# Display final results
sys.stdout.write(f"\n{'='*70}\n")
sys.stdout.write("FINAL RESULTS\n")
sys.stdout.write(f"{'='*70}\n\n")
sys.stdout.write("MISSING SKILLS:\n")
for i, skill in enumerate(missing_skills, 1):
    sys.stdout.write(f"  {i}. {skill.title()}\n")

sys.stdout.write(f"\nSUGGESTED LEARNING RESOURCES:\n")
sys.stdout.write(f"{'='*70}\n")
for skill, resources in resources_dict.items():
    sys.stdout.write(f"\n📚 {skill.upper()}:\n")
    sys.stdout.write("-" * 70 + "\n")
    for i, url in enumerate(resources, 1):
        sys.stdout.write(f"   {i}. {url}\n")

sys.stdout.write(f"\n{'='*70}\n")
sys.stdout.write("SUMMARY\n")
sys.stdout.write(f"{'='*70}\n")
sys.stdout.write(f"  • Missing Skills: {len(missing_skills)}\n")
total_resources = sum(len(r) for r in resources_dict.values())
sys.stdout.write(f"  • Total Resources Found: {total_resources}\n")
sys.stdout.write(f"  • SERP API Status: {'Active ✓' if ge.use_serpapi else 'Using Fallback'}\n")
sys.stdout.write(f"{'='*70}\n\n")
sys.stdout.flush()

