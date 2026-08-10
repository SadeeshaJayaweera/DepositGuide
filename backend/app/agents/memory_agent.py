import json
import math
from typing import List
from sqlmodel import Session, select
from pydantic import BaseModel
from app.models import UserMemory
from app.llm.client import LLMClient

def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def extract_and_save_facts(user_id: int, message: str, session: Session, llm_client: LLMClient):
    """
    Extracts persistent personal facts from the user's message and saves them to the UserMemory table.
    """
    system_prompt = (
        "You are a memory extraction agent for a financial advisor app. "
        "Your task is to analyze the user's message and extract any long-term, persistent facts, "
        "preferences, or goals about the user (e.g., 'I get paid on the 15th', 'I am a freelancer', 'I want to save for a car'). "
        "Only extract facts about the user. Do not extract temporary questions or greetings. "
        "Output the result as JSON."
    )
    
    try:
        response_text = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=message,
            response_mime_type="application/json"
        )
        data = json.loads(response_text)
        
        # Handle cases where LLM returns a dictionary with 'facts' key, or just a list.
        # Fallback to standard Pydantic model structure expectation if possible.
        # But we're just parsing JSON dynamically for safety.
        facts_list = data.get("facts", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        
        for fact in facts_list:
            if not isinstance(fact, str):
                continue
            
            # Check if this fact is already vaguely in the DB by exact match (or we could rely on RAG to dedupe later)
            existing = session.exec(
                select(UserMemory).where(UserMemory.user_id == user_id, UserMemory.fact == fact)
            ).first()
            
            if not existing:
                embedding = llm_client.embed(fact)
                if embedding:
                    mem = UserMemory(
                        user_id=user_id,
                        fact=fact,
                        embedding_json=json.dumps(embedding)
                    )
                    session.add(mem)
        
        session.commit()
    except Exception as e:
        print(f"Memory extraction failed: {e}")


def retrieve_relevant_facts(user_id: int, query: str, session: Session, llm_client: LLMClient, top_k: int = 5) -> List[str]:
    """
    Retrieves the top_k most relevant facts for the given query from the user's memory.
    """
    query_embedding = llm_client.embed(query)
    if not query_embedding:
        return []
        
    memories = session.exec(select(UserMemory).where(UserMemory.user_id == user_id)).all()
    if not memories:
        return []
        
    scored_memories = []
    for mem in memories:
        try:
            mem_emb = json.loads(mem.embedding_json)
            score = _cosine_similarity(query_embedding, mem_emb)
            scored_memories.append((score, mem.fact))
        except Exception:
            continue
            
    # Sort by score descending
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    
    # Return top K facts that have a decent similarity score (e.g. > 0.5)
    return [fact for score, fact in scored_memories[:top_k] if score > 0.5]
