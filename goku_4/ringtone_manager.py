import os
import wave
import struct
import math
import subprocess

class RingtoneManager:
    def __init__(self, ringtone_dir="ringtones"):
        self.ringtone_dir = ringtone_dir
        os.makedirs(ringtone_dir, exist_ok=True)
        self._generate_all()

    def _generate_wav(self, path, samples):
        with wave.open(path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            data = struct.pack('<' + 'h' * len(samples), *samples)
            wav.writeframes(data)

    def _generate_alarm(self):
        samples = []
        for burst in range(8):
            freq = 800 + burst * 100
            for i in range(44100 // 4):
                t = i / 44100
                val = int(20000 * math.sin(2 * math.pi * freq * t))
                samples.append(val)
            samples.extend([0] * (44100 // 8))
        self._generate_wav(os.path.join(self.ringtone_dir, "alarm.wav"), samples)

    def _generate_timer(self):
        samples = []
        notes = [523, 659, 784, 1047]
        for freq in notes:
            for i in range(44100 // 2):
                t = i / 44100
                val = int(20000 * math.sin(2 * math.pi * freq * t))
                samples.append(val)
        self._generate_wav(os.path.join(self.ringtone_dir, "timer.wav"), samples)

    def _generate_notification(self):
        samples = []
        for i in range(44100 // 10):
            t = i / 44100
            val = int(15000 * math.sin(2 * math.pi * 1000 * t))
            samples.append(val)
        self._generate_wav(os.path.join(self.ringtone_dir, "notification.wav"), samples)

    def _generate_all(self):
        self._generate_alarm()
        self._generate_timer()
        self._generate_notification()

    def play_alarm(self):
        self.play_file(os.path.join(self.ringtone_dir, "alarm.wav"))

    def play_timer(self):
        self.play_file(os.path.join(self.ringtone_dir, "timer.wav"))

    def play_notification(self):
        self.play_file(os.path.join(self.ringtone_dir, "notification.wav"))

    def play_file(self, path):
        try:
            subprocess.run(["paplay", path], check=False, timeout=30)
        except Exception as e:
            print(f"Playback error: {e}")

ringtone_manager = RingtoneManager()
