import speech_recognition as sr
import logging
import os
import subprocess
import tempfile

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "alsa"

logger = logging.getLogger('GOKU.Speech')

class SpeechRecognition:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.device = "plughw:2,0"  # USB Mic ALSA device

    def initialize(self, device=None):
        if device:
            self.device = device
        logger.info(f"Speech system ready (ALSA device: {self.device})")
        return True

    def listen_once(self, timeout=5):
        """Record via arecord CLI to avoid PyAudio segfaults."""
        wav_path = tempfile.mktemp(suffix=".wav")
        try:
            # Record using ALSA arecord (bypasses PortAudio/pyaudio)
            cmd = [
                "arecord", "-D", self.device, "-f", "S16_LE",
                "-r", "16000", "-d", str(timeout), "-q", wav_path
            ]
            logger.info(f"Recording {timeout}s via arecord...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0 or not os.path.exists(wav_path) or os.path.getsize(wav_path) < 100:
                logger.warning(f"arecord failed or empty: {result.stderr}")
                return None

            # Recognize via Google
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized: {text}")
            return text.lower().strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Google API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Listen error: {e}")
            return None
        finally:
            if os.path.exists(wav_path):
                os.remove(wav_path)

speech_recognition = SpeechRecognition()
