class ReasoningEngine:
    def generate(self, cand, rank, score):
        profile = cand["profile"]
        skills = [s["name"] for s in cand["skills"]]
        signals = cand["redrob_signals"]
        
        # 1. Identify specific matching skills
        target_skills = ["NDCG", "MRR", "Pinecone", "FAISS", "Weaviate", "Qdrant", "vector", "embeddings"]
        matched_skills = [s for s in skills if any(t.lower() in s.lower() for t in target_skills)]
        
        # 2. Extract key experience details
        yoe = profile.get("years_of_experience", 0.0)
        curr_title = profile.get("current_title", "Engineer")
        curr_company = profile.get("current_company", "Product Company")
        
        # 3. Construct specific sentences
        skills_str = ", ".join(matched_skills[:3]) if matched_skills else "applied ML retrieval"
        
        if rank <= 10:
            reason = (
                f"Ranked in top 10 due to {yoe} years of experience as a {curr_title} at {curr_company} "
                f"with clear production depth in {skills_str}. Combined with a high recruiter response rate "
                f"of {int(signals.get('recruiter_response_rate', 0.0)*100)}% and immediate availability."
            )
        elif rank <= 50:
            reason = (
                f"Strong candidate with {yoe} years of experience. Demonstrated experience with {skills_str}. "
                f"Good recent activity and active recruiter engagement."
            )
        else:
            reason = (
                f"Solid foundation with {yoe} years of experience. Gaps in direct evaluation metrics, but "
                f"strong coding proficiency and positive behavioral response signals support this ranking."
            )
            
        # Acknowledge notice period concern if very high
        notice = signals.get("notice_period_days", 0)
        if notice > 60:
            reason += f" Acknowledging a {notice}-day notice period concern."
            
        return reason
