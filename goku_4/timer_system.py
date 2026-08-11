import threading
import time
from ringtone_manager import ringtone_manager

class Timer:
    def __init__(self, name, seconds, tts):
        self.name = name
        self.seconds = seconds
        self.tts = tts
        self.remaining = seconds
        self.running = False
        self.paused = False
        self.done = False
        self._thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.paused = False
        self.done = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self.running and self.remaining > 0:
            if not self.paused:
                time.sleep(1)
                self.remaining -= 1
            else:
                time.sleep(0.1)
        if self.remaining <= 0 and self.running:
            self.running = False
            self.done = True
            self._on_complete()

    def _on_complete(self):
        ringtone_manager.play_timer()
        time.sleep(0.3)
        if self.tts:
            self.tts.speak(f"Timer {self.name} is done!")

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False

class TimerSystem:
    def __init__(self):
        self.timers = {}
        self.tts = None
        self._lock = threading.Lock()

    def initialize(self, tts=None):
        if tts:
            self.tts = tts

    def create_timer(self, name, seconds):
        with self._lock:
            timer = Timer(name, seconds, self.tts)
            self.timers[name] = timer
            return timer

    def start_timer(self, name):
        with self._lock:
            if name in self.timers:
                self.timers[name].start()
                return True
        return False

    def stop_timer(self, name):
        with self._lock:
            if name in self.timers:
                self.timers[name].stop()
                del self.timers[name]
                return True
        return False

    def pause_timer(self, name):
        with self._lock:
            if name in self.timers:
                self.timers[name].pause()
                return True
        return False

    def resume_timer(self, name):
        with self._lock:
            if name in self.timers:
                self.timers[name].resume()
                return True
        return False

    def list_timers(self):
        with self._lock:
            return {name: {"remaining": t.remaining, "running": t.running, "paused": t.paused}
                    for name, t in self.timers.items() if t.running or not t.done}

    def stop_all(self):
        with self._lock:
            for timer in self.timers.values():
                timer.stop()
            self.timers.clear()

timer_system = TimerSystem()
