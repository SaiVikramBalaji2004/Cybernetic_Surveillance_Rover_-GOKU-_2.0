import logging
from typing import Optional
from config import GOOGLE_API_KEY

logger = logging.getLogger('GOKU.Gemini')

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI SDK not available")

class GeminiAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or GOOGLE_API_KEY
        self.client = None
        self.model_name = 'gemini-1.5-flash'
        self.chat_history = []
        self.current_system_prompt = None

    def initialize(self):
        if not GEMINI_AVAILABLE:
            logger.error("Gemini SDK not available")
            return False
        if not self.api_key:
            logger.error("No API key")
            return False
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini Text assistant initialized")
            return True
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
            return False

    def _ensure_session(self, system_prompt=None):
        if system_prompt and system_prompt != self.current_system_prompt:
            self.current_system_prompt = system_prompt
            self.chat_history = [
                {"role": "user", "parts": [{"text": system_prompt}]},
                {"role": "model", "parts": [{"text": "Understood."}]}
            ]
        elif not self.chat_history:
            self.chat_history = []

    def chat(self, message, system_prompt=None):
        if not self.client:
            return None
        try:
            self._ensure_session(system_prompt)
            content = self.chat_history + [{"role": "user", "parts": [{"text": message}]}]
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=content
            )
            if response.text:
                self.chat_history.append({"role": "user", "parts": [{"text": message}]})
                self.chat_history.append({"role": "model", "parts": [{"text": response.text}]})
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            return None

    def ask(self, question):
        return self.chat(question, system_prompt="Answer the question directly and accurately. Do not add greetings, filler, or extra commentary. Give only the factual answer. 1-3 sentences max.")

    def clear_history(self):
        self.chat_history = []
        self.current_system_prompt = None

gemini_assistant = GeminiAssistant()
