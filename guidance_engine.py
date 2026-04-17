from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from nlp.nlp_intake import CandidateToken, NLPIntakePipeline
from ml_pipeline import ResumeMLPipeline

try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    GoogleSearch = None


# Minimal core skill sets per category (example for existing categories).
# In a real system, these should be derived from data or a curated skill matrix.
CORE_SKILLS_BY_CATEGORY: Dict[str, List[str]] = {
    "Data Science": [
        "python",
        "machine learning",
        "data analysis",
        "sql",
        "deep learning",
        "natural language processing",
    ],
    "Web Designing": [
        "javascript",
        "react",
        "css",
        "html",
    ],
    "Advocate": [
        "legal research",
        "contract law",
    ],
    "Arts": [
        "graphic design",
    ],
    "HR": [
        "recruitment",
        "people management",
    ],
    "Mechanical Engineer": [
        "cad",
        "solidworks",
    ],
}


@dataclass
class GuidanceResult:
    missing_skills: List[str]
    suggested_resources: Dict[str, List[str]]
    neighbor_skills: Optional[List[str]] = None  # Skills from k-NN neighbors
    method: str = "static"  # "kmeans" or "static"


class GuidanceEngine:
    """Enhanced guidance engine using k-means/k-NN as described in development_plan_ml_model.md.

    Given a candidate token and a target category, it computes missing skills using:
    1. k-NN to find similar successful candidates (if ML pipeline provided)
    2. Fallback to static core skill sets per category
    
    Can use SERP API for real-time, accurate course and learning resource results.
    """

    def __init__(
        self, 
        core_skills_by_category: Dict[str, List[str]] | None = None,
        serpapi_key: Optional[str] = None,
        use_serpapi: bool = True,
        ml_pipeline: Optional[ResumeMLPipeline] = None,
        training_df: Optional[pd.DataFrame] = None,
        training_vectors: Optional[np.ndarray] = None,
    ) -> None:
        self.core_skills_by_category = core_skills_by_category or CORE_SKILLS_BY_CATEGORY
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        self.use_serpapi = use_serpapi and SERPAPI_AVAILABLE and self.serpapi_key is not None
        
        # ML pipeline components for k-NN based guidance
        self.ml_pipeline = ml_pipeline
        self.training_df = training_df
        self.training_vectors = training_vectors
        self.nlp_pipeline = NLPIntakePipeline() if ml_pipeline else None

    def compute_missing_skills_kmeans(
        self,
        candidate: CandidateToken,
        category: str,
        k_neighbors: int = 5,
        top_n: int = 10,
    ) -> Tuple[List[str], List[str]]:
        """Compute missing skills using k-NN from successful candidates in the same category.
        
        Returns:
            Tuple of (missing_skills, neighbor_skills_found)
        """
        if not (self.ml_pipeline and self.training_df is not None):
            raise ValueError("ML pipeline and training_df required for k-means guidance")
        
        if self.ml_pipeline.kNN is None:
            raise ValueError("ML pipeline kNN not fitted. Call fit_clusters first.")
        
        # Build candidate's feature vector
        semantic_vec = candidate.embedding.reshape(1, -1)
        structured_vec = self.ml_pipeline.transform_structured_row(
            years_experience=candidate.experience,
            projects_count=candidate.projects,
            certificates_count=candidate.certifications,
        )
        candidate_vec = self.ml_pipeline.fuse_features(semantic_vec, structured_vec)[0]
        
        # Find k nearest neighbors
        neighbor_indices = self.ml_pipeline.nearest_neighbors(candidate_vec, k=k_neighbors)
        
        # Filter neighbors by category and success (if 'selected' column exists)
        candidate_skills = {s.lower() for s in candidate.skills}
        neighbor_skills_all = []
        
        for idx in neighbor_indices:
            if idx >= len(self.training_df):
                continue
            
            row = self.training_df.iloc[idx]
            # Only consider neighbors in the same category
            if str(row.get("category", "")).lower() != category.lower():
                continue
            
            # Optionally filter by success (if 'selected' column exists)
            if "selected" in row and row["selected"] != 1:
                continue
            
            # Extract skills from neighbor's resume text
            resume_text = str(row.get("resume_text", ""))
            if resume_text:
                try:
                    neighbor_token = self.nlp_pipeline.build_candidate_token_from_text(resume_text)
                    neighbor_skills_all.extend(neighbor_token.skills)
                except Exception:
                    # Fallback: try to extract skills using regex if build_candidate_token fails
                    # This is a simplified extraction
                    pass
        
        # Count skill frequency in neighbors
        from collections import Counter
        skill_counts = Counter(s.lower() for s in neighbor_skills_all)
        
        # Find skills present in neighbors but missing from candidate
        missing = []
        for skill, count in skill_counts.most_common():
            if skill.lower() not in candidate_skills and skill.strip():
                missing.append(skill)
        
        neighbor_skills_list = [s for s, _ in skill_counts.most_common(top_n * 2)]
        
        return missing[:top_n], neighbor_skills_list[:top_n * 2]

    def compute_missing_skills(
        self,
        candidate: CandidateToken,
        category: str,
        top_n: int = 10,
        use_kmeans: bool = True,
    ) -> Tuple[List[str], Optional[List[str]], str]:
        """Return a list of missing skills for the candidate in the target category.
        
        Args:
            candidate: Candidate token
            category: Target category
            top_n: Maximum number of missing skills to return
            use_kmeans: If True and ML pipeline available, use k-NN method; else use static list
            
        Returns:
            Tuple of (missing_skills, neighbor_skills, method_used)
        """
        # Try k-means/k-NN method first if available
        if use_kmeans and self.ml_pipeline and self.training_df is not None:
            try:
                missing, neighbor_skills = self.compute_missing_skills_kmeans(
                    candidate, category, k_neighbors=5, top_n=top_n
                )
                if missing:  # Only return if we found skills via k-NN
                    return missing, neighbor_skills, "kmeans"
            except Exception as e:
                print(f"Warning: k-means guidance failed: {e}. Falling back to static method.")
        
        # Fallback to static method
        candidate_skills = {s.lower() for s in candidate.skills}
        core = {s.lower() for s in self.core_skills_by_category.get(category, [])}
        missing = [s for s in core if s not in candidate_skills]
        return missing[:top_n], None, "static"

    def _suggest_resources_for_skill(self, skill: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Return diverse learning resources for a given skill using SERP API.
        
        Searches for multiple resource types: courses, tutorials, certifications, books, and practice platforms.
        Uses SERP API to get real-time, accurate results from search engines.
        Falls back to template URLs if SERP API is not available or fails.
        
        Args:
            skill: The skill name to search for
            max_results: Maximum number of results to return
            
        Returns:
            List of resource dicts with 'title', 'link', and 'type'
        """
        if self.use_serpapi:
            resources = []
            seen_links = set()  # Avoid duplicates
            
            # Define multiple search queries for different resource types
            search_queries = [
                (f"{skill} course", "course"),
                (f"{skill} tutorial", "tutorial"),
                (f"{skill} certification", "certification"),
                (f"{skill} book", "book"),
                (f"learn {skill} online", "course"),
            ]
            
            # Limit queries to avoid too many API calls
            queries_to_use = search_queries[:3]  # Use first 3 queries
            
            for query_text, resource_type in queries_to_use:
                if len(resources) >= max_results:
                    break
                    
                try:
                    params = {
                        "q": query_text,
                        "api_key": self.serpapi_key,
                        "engine": "google",
                        "num": min(10, max_results * 2),  # Get more results to filter
                    }
                    
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    # Extract organic search results
                    if "organic_results" in results:
                        for result in results["organic_results"]:
                            if len(resources) >= max_results:
                                break
                                
                            link = result.get("link", "")
                            if link and link not in seen_links:
                                # Filter for learning platforms
                                learning_domains = [
                                    "coursera", "udemy", "edx", "khan", "pluralsight", 
                                    "linkedin", "youtube", "udacity", "codecademy",
                                    "freecodecamp", "w3schools", "tutorialspoint",
                                    "amazon", "oreilly", "packt", "skillshare"
                                ]
                                
                                # Check if link is from a learning platform or contains learning keywords
                                is_learning_resource = any(
                                    domain in link.lower() for domain in learning_domains
                                ) or any(
                                    keyword in result.get("title", "").lower() 
                                    for keyword in ["course", "tutorial", "learn", "certification", "training"]
                                )
                                
                                if is_learning_resource:
                                    seen_links.add(link)
                                    resources.append({
                                        "title": result.get("title", f"Learn {skill}"),
                                        "link": link,
                                        "type": resource_type,
                                        "snippet": result.get("snippet", "")[:150]  # Preview text
                                    })
                
                        # Extract shopping results (for courses on platforms like Udemy, Coursera)
                        if len(resources) < max_results and "shopping_results" in results:
                            for item in results["shopping_results"][:3]:
                                if len(resources) >= max_results:
                                    break
                                    
                                link = item.get("link", "")
                                if link and link not in seen_links:
                                    # Only include if it's from a known learning platform
                                    learning_domains = ["coursera", "udemy", "edx", "skillshare", "pluralsight"]
                                    if any(domain in link.lower() for domain in learning_domains):
                                        seen_links.add(link)
                                        resources.append({
                                            "title": item.get("title", f"{skill} Course"),
                                            "link": link,
                                            "type": "course",
                                            "snippet": item.get("price", "")
                                        })
                    
                        # Extract knowledge graph results if available
                        if len(resources) < max_results and "knowledge_graph" in results:
                            kg = results["knowledge_graph"]
                            if "courses" in kg:
                                for course in kg["courses"][:2]:
                                    if len(resources) >= max_results:
                                        break
                                    link = course.get("link", "")
                                    if link and link not in seen_links:
                                        seen_links.add(link)
                                        resources.append({
                                            "title": course.get("name", f"{skill} Course"),
                                            "link": link,
                                            "type": "course",
                                            "snippet": ""
                                        })
                    
                except Exception as e:
                    # Continue with next query if one fails
                    print(f"Warning: SERP API query '{query_text}' failed: {e}")
                    continue
            
            # If we got results, return them
            if resources:
                return resources[:max_results]
        
        # Fallback to template URLs if SERP API is not available or fails
        skill_slug = skill.replace(" ", "+")
        return [
            {
                "title": f"Coursera: {skill} Courses",
                "link": f"https://www.coursera.org/search?query={skill_slug}",
                "type": "course",
                "snippet": "Browse courses on Coursera"
            },
            {
                "title": f"Udemy: {skill} Courses",
                "link": f"https://www.udemy.com/courses/search/?q={skill_slug}",
                "type": "course",
                "snippet": "Browse courses on Udemy"
            },
            {
                "title": f"YouTube: {skill} Tutorials",
                "link": f"https://www.youtube.com/results?search_query={skill_slug}+tutorial",
                "type": "tutorial",
                "snippet": "Watch video tutorials on YouTube"
            },
            {
                "title": f"edX: {skill} Courses",
                "link": f"https://www.edx.org/search?q={skill_slug}",
                "type": "course",
                "snippet": "Browse courses on edX"
            },
            {
                "title": f"FreeCodeCamp: {skill}",
                "link": f"https://www.freecodecamp.org/news/search/?query={skill_slug}",
                "type": "tutorial",
                "snippet": "Free coding tutorials and articles"
            },
        ]

    def generate_guidance(
        self,
        candidate: CandidateToken,
        category: str,
        top_n: int = 10,
        use_kmeans: bool = True,
    ) -> GuidanceResult:
        """Generate guidance using k-means/k-NN if available, otherwise static method."""
        missing, neighbor_skills, method = self.compute_missing_skills(
            candidate, category, top_n=top_n, use_kmeans=use_kmeans
        )
        resources: Dict[str, List[Dict[str, str]]] = {
            skill: self._suggest_resources_for_skill(skill) for skill in missing
        }
        return GuidanceResult(
            missing_skills=missing,
            suggested_resources=resources,
            neighbor_skills=neighbor_skills,
            method=method
        )
