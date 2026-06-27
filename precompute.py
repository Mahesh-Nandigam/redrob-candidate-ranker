import os
import json
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import argparse

# 1. Load Embedding Model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Define traps
CONSULTING_COMPANIES = {
    "tcs", "wipro", "infosys", "capgemini", "accenture", 
    "cognizant", "tech mahindra", "mphasis"
}

PRODUCT_COMPANIES = {
    "zomato", "swiggy", "cred", "razorpay", "flipkart", "meesho", 
    "nykaa", "inmobi", "byju's", "policybazaar", "ola", "zoho", 
    "vedantu", "paytm", "unacademy", "pharmeasy", "upgrad", 
    "freshworks", "phonepe", "dream11", "google", "amazon", 
    "meta", "microsoft", "apple", "netflix"
}

def check_honeypots(cand):
    career = cand.get("career_history", [])
    skills = cand.get("skills", [])
    
    # Timeline traps
    for job in career:
        comp = job.get("company", "")
        start_date = job.get("start_date", "")
        if not start_date:
            continue
        try:
            start_year = int(start_date.split("-")[0])
        except ValueError:
            continue
            
        if comp == "Sarvam AI" and start_year < 2023:
            return True
        if comp == "Krutrim" and start_year < 2023:
            return True
        if comp == "CRED" and start_year < 2018:
            return True
        if comp == "Glance" and start_year < 2019:
            return True
            
    # Skill traps
    for s in skills:
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 0:
            return True
            
    return False

def check_consulting_only(cand):
    career = cand.get("career_history", [])
    has_consulting = False
    has_product = False
    for job in career:
        comp = job.get("company", "").lower()
        if any(c in comp for c in CONSULTING_COMPANIES):
            has_consulting = True
        if any(p in comp for p in PRODUCT_COMPANIES):
            has_product = True
    return has_consulting and not has_product

def check_title_chaser(cand):
    career = cand.get("career_history", [])
    if len(career) >= 3:
        tenures = [job.get("duration_months", 0) for job in career]
        avg_tenure = sum(tenures) / len(tenures) if tenures else 0
        if avg_tenure < 18:
            return True
    return False

def extract_dense_text(cand):
    profile = cand.get("profile", {})
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")
    skills_list = ", ".join([s.get("name", "") for s in cand.get("skills", [])])
    
    jobs_list = []
    for job in cand.get("career_history", []):
        jobs_list.append(f"{job.get('title', '')} at {job.get('company', '')}: {job.get('description', '')}")
    jobs_text = " | ".join(jobs_list)
    
    return f"{headline} {summary} Skills: {skills_list} History: {jobs_text}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory containing candidates.jsonl")
    args = parser.parse_args()

    candidates_metadata = []
    texts_to_embed = []
    
    # Use the passed data_dir
    data_path = os.path.join(args.data_dir, "candidates.jsonl")
    
    if not os.path.exists(data_path):
        print(f"ERROR: Could not find {data_path}.")
        print(f"Please ensure the organizer's dataset is placed at {data_path}")
        exit(1)
        
    print(f"Reading dataset from {data_path}...")
    with open(data_path, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if not line.strip():
                continue
            cand = json.loads(line)
            cid = cand["candidate_id"]
            
            # Calc Flags
            is_honeypot = check_honeypots(cand)
            is_consulting_only = check_consulting_only(cand)
            is_title_chaser = check_title_chaser(cand)
            
            # Save metadata fields
            signals = cand.get("redrob_signals", {})
            candidates_metadata.append({
                "candidate_id": cid,
                "name": cand["profile"].get("anonymized_name"),
                "years_of_experience": cand["profile"].get("years_of_experience", 0.0),
                "recruiter_response_rate": signals.get("recruiter_response_rate", 0.0),
                "last_active_date": signals.get("last_active_date", ""),
                "interview_completion_rate": signals.get("interview_completion_rate", 0.0),
                "notice_period_days": signals.get("notice_period_days", 90),
                "is_honeypot": is_honeypot,
                "is_consulting_only": is_consulting_only,
                "is_title_chaser": is_title_chaser,
                "candidate_json": json.dumps(cand) # Save full json string to avoid loading jsonl in rank.py
            })
            
            texts_to_embed.append(extract_dense_text(cand))

    # 4. Generate Embeddings and Save FAISS Index
    print(f"Generating embeddings for {len(texts_to_embed)} candidates (this may take a few minutes)...")
    embeddings = model.encode(texts_to_embed, show_progress_bar=True, batch_size=256)
    embeddings = np.array(embeddings).astype("float32")

    # Normalize for Cosine Similarity
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, "candidate_vectors.faiss")

    # 5. Save Parquet
    df = pd.DataFrame(candidates_metadata)
    df.to_parquet("candidate_metadata.parquet")
    print("Pre-computation completed successfully.")
