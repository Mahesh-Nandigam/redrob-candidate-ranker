import argparse
import pandas as pd
import numpy as np
import faiss
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
from reasoning import ReasoningEngine

# Core search terms for Sparse scoring
SPARSE_KEYWORDS = [
    "ndcg", "mrr", "map", "pinecone", "faiss", "weaviate", "qdrant", 
    "milvus", "hybrid search", "sentence-transformers", "embeddings", 
    "ranking", "retrieval"
]

def calculate_sparse_score(json_str):
    cand = json.loads(json_str)
    text = (cand["profile"].get("summary", "") + " " + 
            " ".join([s["name"] for s in cand["skills"]]) + " " +
            " ".join([j["description"] for j in cand["career_history"]])).lower()
    
    matches = sum(1 for word in SPARSE_KEYWORDS if word in text)
    return min(matches / len(SPARSE_KEYWORDS), 1.0)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--out", required=True, help="Path to output CSV")
    args = parser.parse_args()
    
    # 1. Load Index and Metadata (Takes < 10 seconds)
    print("Loading FAISS index and metadata...")
    index = faiss.read_index("candidate_vectors.faiss")
    df = pd.read_parquet("candidate_metadata.parquet")
    
    # 2. Embed Job Description (Target: Senior AI Engineer Founding Team)
    jd_query = (
        "Senior AI Engineer Founding Team. Production embeddings-based retrieval systems, "
        "sentence-transformers, vector databases, hybrid search, Pinecone, FAISS, Weaviate, Qdrant. "
        "Evaluation frameworks ranking systems NDCG, MRR, MAP. Python product developer."
    )
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vector = model.encode([jd_query]).astype("float32")
    faiss.normalize_L2(query_vector)
    
    # 3. Retrieve Top 3,000 candidates using FAISS (Takes < 2 seconds)
    print("Retrieving candidate matches...")
    distances, indices = index.search(query_vector, 3000)
    
    top_indices = indices[0]
    top_distances = distances[0]
    
    # Filter metadata to top 3,000 matches
    results_df = df.iloc[top_indices].copy()
    results_df["dense_similarity"] = top_distances
    
    # 4. Calculate Sparse and Final Hybrid Score (Takes ~10 seconds)
    print("Scoring and ranking candidates...")
    results_df["sparse_score"] = results_df["candidate_json"].apply(calculate_sparse_score)
    
    # Calculate baseline hybrid score (40% dense, 60% sparse)
    results_df["score"] = 0.40 * results_df["dense_similarity"] + 0.60 * results_df["sparse_score"]
    
    # 5. Apply Trap Penalties and Behavioral Signals
    scores = []
    current_date = datetime(2026, 6, 27)
    
    for idx, row in results_df.iterrows():
        # Disqualify honeypots immediately
        if row["is_honeypot"]:
            scores.append(0.0)
            continue
            
        score = row["score"]
        
        # Penalties
        if row["is_consulting_only"]:
            score -= 0.30
        if row["is_title_chaser"]:
            score -= 0.15
            
        # Notice Period Adjustment (Progressive Penalty)
        if row["notice_period_days"] > 60:
            score -= 0.10
            
        # Last active date calculation
        try:
            active_date = datetime.strptime(row["last_active_date"], "%Y-%m-%d")
            days_inactive = (current_date - active_date).days
        except Exception:
            days_inactive = 365
            
        # Behavioral Signals boosts and penalties
        if row["recruiter_response_rate"] > 0.80 and days_inactive <= 30:
            score += 0.15
        elif row["interview_completion_rate"] < 0.50 or days_inactive > 180:
            score -= 0.20
            
        scores.append(max(0.0, score))
        
    results_df["score"] = scores
    
    # 6. Sort by Score (DESC) and candidate_id (ASC) for tie-breaking
    results_df = results_df.sort_values(by=["score", "candidate_id"], ascending=[False, True])
    
    # Select Top 100
    top_100 = results_df.head(100).copy()
    
    # 7. Generate Non-hallucinated Reasonings
    print("Generating justifications...")
    engine = ReasoningEngine()
    reasons = []
    rank = 1
    
    for idx, row in top_100.iterrows():
        cand = json.loads(row["candidate_json"])
        reason = engine.generate(cand, rank, row["score"])
        reasons.append(reason)
        rank += 1
        
    top_100["reasoning"] = reasons
    top_100["rank"] = np.arange(1, 101)
    
    # Save exact required columns
    output_df = top_100[["candidate_id", "rank", "score", "reasoning"]]
    output_df.to_csv(args.out, index=False)
    print(f"Top 100 output saved successfully to {args.out}")

if __name__ == "__main__":
    main()
