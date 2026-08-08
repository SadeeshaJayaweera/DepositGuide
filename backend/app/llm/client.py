import os
from typing import Protocol
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass

class GeminiLLMClient(LLMClient):
    def __init__(self):
        # We rely on GEMINI_API_KEY being in the environment
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
            ),
        )
        return response.text

class FakeLLMClient(LLMClient):
    def __init__(self, canned_response: str = "{}"):
        self.canned_response = canned_response
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.canned_response

def get_llm_client() -> LLMClient:
    return GeminiLLMClient()
