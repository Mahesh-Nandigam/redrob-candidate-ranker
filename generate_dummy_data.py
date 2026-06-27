import gzip
import json

candidates = [
    {
        "candidate_id": "CAND-001",
        "profile": {
            "anonymized_name": "Candidate A (The Perfect Match)",
            "headline": "Senior AI Engineer",
            "summary": "Experienced AI Engineer specializing in retrieval architectures, FAISS, and LLM orchestration.",
            "years_of_experience": 6.5
        },
        "skills": [
            {"name": "Python", "proficiency": "expert", "duration_months": 72},
            {"name": "FAISS", "proficiency": "expert", "duration_months": 48},
            {"name": "Sentence-Transformers", "proficiency": "advanced", "duration_months": 36}
        ],
        "career_history": [
            {"title": "Senior AI Engineer", "company": "Razorpay", "start_date": "2020-01-01", "duration_months": 48, "description": "Built scalable vector search pipelines using FAISS."}
        ],
        "redrob_signals": {
            "recruiter_response_rate": 0.95,
            "last_active_date": "2024-05-01",
            "interview_completion_rate": 1.0,
            "notice_period_days": 30
        }
    },
    {
        "candidate_id": "CAND-002",
        "profile": {
            "anonymized_name": "Candidate B (The Honeypot / Fake)",
            "headline": "AI Expert",
            "summary": "I am an expert in all things AI.",
            "years_of_experience": 10.0
        },
        "skills": [
            {"name": "FAISS", "proficiency": "expert", "duration_months": 0} # SKILL TRAP: Expert with 0 months
        ],
        "career_history": [
            {"title": "Founding Engineer", "company": "Sarvam AI", "start_date": "2019-01-01", "duration_months": 12, "description": "Founded the company before it existed."} # TIMELINE TRAP
        ],
        "redrob_signals": {
            "recruiter_response_rate": 0.10,
            "notice_period_days": 0
        }
    },
    {
        "candidate_id": "CAND-003",
        "profile": {
            "anonymized_name": "Candidate C (The Title Chaser)",
            "headline": "Director of AI",
            "summary": "Fast learner, moving up quickly.",
            "years_of_experience": 2.5
        },
        "skills": [
            {"name": "Python", "proficiency": "intermediate", "duration_months": 12}
        ],
        "career_history": [
            {"title": "AI Engineer", "company": "TCS", "start_date": "2022-01-01", "duration_months": 8, "description": "AI stuff."},
            {"title": "Lead AI Engineer", "company": "Wipro", "start_date": "2022-09-01", "duration_months": 7, "description": "More AI stuff."},
            {"title": "Director of AI", "company": "Infosys", "start_date": "2023-04-01", "duration_months": 5, "description": "Leading AI."}
        ],
        "redrob_signals": {
            "recruiter_response_rate": 0.90,
            "notice_period_days": 30
        }
    }
]

with gzip.open("candidates.jsonl.gz", "wt", encoding="utf-8") as f:
    for c in candidates:
        f.write(json.dumps(c) + "\n")

print("Created candidates.jsonl.gz successfully!")
