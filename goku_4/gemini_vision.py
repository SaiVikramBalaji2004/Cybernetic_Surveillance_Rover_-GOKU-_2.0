import io
import time
import logging
from config import GOOGLE_VISION_API_KEY

logger = logging.getLogger('GOKU.GeminiVision')

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google GenAI SDK not available")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class GeminiVision:
    def __init__(self, api_key=None):
        self.api_key = api_key or GOOGLE_VISION_API_KEY
        self.client = None
        self.model_name = 'gemini-1.5-flash'

    def initialize(self):
        if not GEMINI_AVAILABLE:
            logger.error("Gemini SDK not available")
            return False
        if not self.api_key:
            logger.error("No API key")
            return False
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Gemini Vision initialized")
            return True
        except Exception as e:
            logger.error(f"Gemini Vision init failed: {e}")
            return False

    def analyze(self, image_bytes, prompt, system_prompt=None, max_retries=2):
        if not self.client:
            logger.error("Vision model not initialized")
            return None
        if not image_bytes:
            logger.error("No image bytes provided")
            return None
        if not PIL_AVAILABLE:
            logger.error("PIL not available for image processing")
            return None

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                image = Image.open(io.BytesIO(image_bytes))
                
                if system_prompt:
                    content = [system_prompt, image, prompt]
                else:
                    content = [prompt, image]

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=content
                )
                result = response.text
                logger.info(f"Vision response received ({len(result)} chars)")
                return result
            except Exception as e:
                last_error = str(e)
                is_quota = "quota" in last_error.lower() or "429" in last_error
                if is_quota and attempt < max_retries:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Gemini quota exceeded, waiting {wait}s (attempt {attempt+1}/{max_retries+1})")
                    time.sleep(wait)
                    continue
                logger.error(f"Gemini vision error: {last_error}")
                break

        if last_error:
            logger.error(f"Gemini vision failed after retries: {last_error}")
        return None

    def describe_scene(self, image_bytes):
        if not self.client or not image_bytes:
            return None
        return self.analyze(
            image_bytes,
            "Describe this scene in one brief sentence. What is in front of the camera?",
            "You are a rover camera. Describe concisely."
        )

    def clear(self):
        self.client = None

gemini_vision = GeminiVision()
