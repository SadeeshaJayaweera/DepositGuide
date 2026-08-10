import pytest
from sqlmodel import Session, create_engine, SQLModel
from app.models import User, UserMemory
from app.agents.memory_agent import extract_and_save_facts, retrieve_relevant_facts
from app.llm.client import LLMClient
import json

class MockLLMClient(LLMClient):
    def __init__(self, expected_facts=None):
        self.expected_facts = expected_facts or []
        self.embedded_texts = []
        
    def generate(self, system_prompt: str, user_prompt: str, response_mime_type: str | None = None) -> str:
        return json.dumps({"facts": self.expected_facts})

    def embed(self, text: str) -> list[float]:
        self.embedded_texts.append(text)
        # Create a deterministic mock embedding
        # e.g. based on hash
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()
        val = int(h, 16) / (16**32)
        # return a vector where the first element determines similarity
        # (This is just a dummy embedding for test)
        if "dog" in text.lower():
            return [1.0, 0.0, 0.0]
        if "freelancer" in text.lower():
            return [0.0, 1.0, 0.0]
        return [0.5, 0.5, 0.5]


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_extract_and_retrieve_facts(session: Session):
    # Setup user
    user = User(email="test@example.com", hashed_password="pwd")
    session.add(user)
    session.commit()
    session.refresh(user)

    # 1. Extract
    llm = MockLLMClient(expected_facts=["I am a freelancer", "I have a dog"])
    extract_and_save_facts(user.id, "I am a freelancer and I have a dog", session, llm)
    
    memories = session.query(UserMemory).all()
    assert len(memories) == 2
    
    # 2. Retrieve
    # query about work (should match freelancer)
    retrieved = retrieve_relevant_facts(user.id, "Am I a freelancer?", session, llm)
    assert len(retrieved) > 0
    assert "I am a freelancer" in retrieved

    # query about pets
    retrieved2 = retrieve_relevant_facts(user.id, "Do I have a dog?", session, llm)
    assert len(retrieved2) > 0
    assert "I have a dog" in retrieved2
