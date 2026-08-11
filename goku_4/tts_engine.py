import logging
import subprocess
import os
import io
import re
import tempfile
import contextlib
from typing import Optional

logger = logging.getLogger('GOKU.TTS')

class TTSEngine:
    def __init__(self):
        self.ready = False
        self.backend = None
        self._init()

    def _init(self):
        try:
            from gtts import gTTS
            self.backend = 'gtts'
            self.ready = True
            logger.info("TTS: gTTS ready (online, natural voice)")
            return
        except ImportError:
            pass

        try:
            result = subprocess.run(['espeak-ng', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.backend = 'espeak-ng'
                self.ready = True
                logger.info("TTS: espeak-ng ready (offline fallback)")
                return
        except Exception as e:
            logger.warning(f"espeak-ng check failed: {e}")

        logger.error("No TTS backend available")

    def initialize(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2)
            logger.info("TTS mixer initialized")
        except Exception as e:
            logger.warning(f"TTS mixer init: {e}")
        return self.ready

    def speak(self, text):
        if not text or not self.ready:
            return
        if self.backend == 'gtts':
            self._speak_gtts(text)
        elif self.backend == 'espeak-ng':
            self._speak_espeak(text)

    def _clean_text(self, text):
        text = re.sub(r'\*\*|\*|`|#|_|~', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if len(text) > 400:
            sentences = re.split(r'(?<=[.!?])\s+', text)
            result = ''
            for s in sentences:
                if len(result) + len(s) > 380:
                    break
                result += s + ' '
            text = result.strip()
        return text

    def _speak_gtts(self, text):
        text = self._clean_text(text)
        if not text:
            return
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en', tld='com')
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                tts.save(f.name)
                self._play_file(f.name)
                try:
                    os.unlink(f.name)
                except:
                    pass
        except Exception as e:
            logger.error(f"gTTS error: {e}, falling back to espeak-ng")
            self.backend = 'espeak-ng'
            self._speak_espeak(text)

    def _speak_espeak(self, text):
        text = self._clean_text(text)
        if not text:
            return
        try:
            cmd = [
                'espeak-ng',
                '-v', 'en-us',
                '-p', '50',
                '-s', '170',
                '--stdout',
                text
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.stdout:
                self._play_audio(result.stdout)
        except Exception as e:
            logger.error(f"espeak-ng error: {e}")

    def _play_file(self, filepath):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2)
            sound = pygame.mixer.Sound(filepath)
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(50)
        except Exception as e:
            logger.error(f"File playback error: {e}")

    def _play_audio(self, audio_data):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
            sound = pygame.mixer.Sound(io.BytesIO(audio_data))
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.wait(50)
        except Exception as e:
            logger.error(f"Audio playback error: {e}")

tts_engine = TTSEngine()
