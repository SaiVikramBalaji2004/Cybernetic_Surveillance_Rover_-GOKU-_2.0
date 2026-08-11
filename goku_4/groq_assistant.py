import logging
from typing import Optional
from config import GROQ_API_KEY

logger = logging.getLogger('GOKU.Groq')

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK not available")

class GroqAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or GROQ_API_KEY
        self.client = None
        self.model = 'llama-3.3-70b-versatile'
        self.conversation_history = []

    def initialize(self):
        if not GROQ_AVAILABLE:
            logger.error("Groq SDK not available")
            return False
        if not self.api_key:
            logger.error("No API key")
            return False
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info("Groq assistant initialized")
            return True
        except Exception as e:
            logger.error(f"Groq init failed: {e}")
            return False

    def chat(self, message, system_prompt=None):
        if not self.client:
            return None
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for msg in self.conversation_history[-10:]:
            messages.append(msg)
        messages.append({"role": "user", "content": message})
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=512
            )
            result = response.choices[0].message.content
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": result})
            return result
        except Exception as e:
            logger.error(f"Groq chat error: {e}")
            return None

    def ask(self, question):
        return self.chat(question, system_prompt="Answer the question directly and accurately. Do not add greetings, filler, or extra commentary. Give only the factual answer. 1-3 sentences max.")

    def clear_history(self):
        self.conversation_history = []

groq_assistant = GroqAssistant()
