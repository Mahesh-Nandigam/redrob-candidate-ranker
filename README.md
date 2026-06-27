# Redrob x Hack2Skill Candidate Ranking System

## Overview
This repository contains our submission for the Redrob candidate ranking challenge. The goal was to build a fast, deterministic, and highly accurate system to evaluate 100,000+ candidate profiles against a specific Job Description under a strict 5-minute CPU constraint.

We engineered a dual-phase hybrid retrieval pipeline that completely separates offline heavy data processing from live inference. This guarantees sub-15-second execution times while maintaining zero hallucinations.

## System Architecture

Our solution is purely backend-driven and relies on the following core components:

1. **Data Ingestion (Apache Parquet & Pandas):** We bypassed slow JSON parsing during inference by structuring the metadata into an optimized columnar format.
2. **Embeddings (Sentence-Transformers):** We used the `all-MiniLM-L6-v2` model to generate high-quality dense vectors locally on CPU, avoiding expensive API calls.
3. **Retrieval (FAISS):** We implemented a local FAISS index (L2 distance) to instantly query the semantic vectors.
4. **Reasoning (Custom Python Engine):** A deterministic evaluation matrix that handles exact keyword matching, behavioral scoring, and trap detection without relying on a generative LLM.

## End-to-End Workflow

1. **Pre-computation (Offline):** 
   - Script: `precompute.py`
   - We process the entire candidate dataset to calculate behavioral flags, detect "Honeypot" timeline traps, and generate semantic embeddings. This data is serialized into Parquet and a FAISS index.

2. **Live Retrieval (Online):** 
   - Script: `rank.py`
   - The system ingests the Job Description, converts it to a vector query, and uses FAISS to retrieve the top 3,000 matches in milliseconds.

3. **Hybrid Scoring:** 
   - We apply a hybrid formula: 40% weight to Dense Vector Similarity and 60% weight to Sparse Keyword Matching (verifying exact technical experience).
   - Behavioral modifiers are applied (e.g., boosting candidates with high recruiter response rates, penalizing job hoppers).

4. **Deterministic Output:** 
   - Script: `reasoning.py`
   - The reasoning engine extracts validated facts directly from the candidate profile to write a transparent, data-backed justification. The final ranked list is exported to `team_shaurya.csv`.

## Explainability and Validation

To ensure absolute accuracy, we completely eliminated generative AI (LLMs) from the real-time ranking step. Our system uses a deterministic template engine that only outputs facts present in the dataset. It is mathematically impossible for our system to hallucinate skills.

Furthermore, we implemented strict **Honeypot Logic**. If a profile contains logical impossibilities (e.g., claiming 5 years of experience at a startup that was founded 1 year ago), it is instantly flagged and disqualified from the top rankings.

## Getting Started

### Prerequisites
- Python 3.9+
- Dependencies listed in `requirements.txt`

### Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Run pre-computation (one-time setup): `python precompute.py`
3. Execute the ranking algorithm: `python rank.py`
4. View the results in the generated `submission.csv`.
