import os
from typing import Protocol
from google import genai
from dotenv import load_dotenv

load_dotenv()

class LLMClient(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, response_mime_type: str | None = None) -> str:
        pass
        
    def embed(self, text: str) -> list[float]:
        pass

class GeminiLLMClient(LLMClient):
    def __init__(self):
        # We rely on GEMINI_API_KEY being in the environment
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate(self, system_prompt: str, user_prompt: str, response_mime_type: str | None = None) -> str:
        if not self.client:
            if response_mime_type == "application/json":
                return '{"explanations": [{"line_item_name": "API Key Missing", "plain_language_explanation": "GEMINI_API_KEY is missing from the backend .env file. Please add it to use AI features."}]}'
            return "⚠️ It looks like your GEMINI_API_KEY is missing from the backend `.env` file. Please add it and restart the backend server to enable the AI Advisor!"

        config_kwargs = {"system_instruction": system_prompt}
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type
            
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=genai.types.GenerateContentConfig(**config_kwargs),
        )
        return response.text

    def embed(self, text: str) -> list[float]:
        if not self.client:
            return []
        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        return response.embeddings[0].values

class FakeLLMClient(LLMClient):
    def __init__(self, canned_response: str = "{}"):
        self.canned_response = canned_response
        self.last_system_prompt = ""
        self.last_user_prompt = ""

    def generate(self, system_prompt: str, user_prompt: str, response_mime_type: str | None = None) -> str:
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        return self.canned_response

    def embed(self, text: str) -> list[float]:
        return [0.0] * 768

def get_llm_client() -> LLMClient:
    return GeminiLLMClient()
