import threading
import time
import datetime
from ringtone_manager import ringtone_manager

class Alarm:
    def __init__(self, name, time_str):
        self.name = name
        self.time_str = time_str
        self.enabled = True
        self.triggered_today = set()

    def should_trigger(self):
        if not self.enabled:
            return False
        now = datetime.datetime.now()
        today = now.date()
        if today in self.triggered_today:
            return False
        current_time = now.strftime("%H:%M")
        if current_time == self.time_str:
            self.triggered_today.add(today)
            return True
        return False

class AlarmSystem:
    def __init__(self):
        self.alarms = []
        self.tts = None
        self._lock = threading.Lock()
        self._thread = None
        self._running = False

    def initialize(self, tts=None):
        if tts:
            self.tts = tts

    def add_alarm(self, name, time_str):
        try:
            datetime.datetime.strptime(time_str, "%H:%M")
            with self._lock:
                self.alarms.append(Alarm(name, time_str))
            return True
        except ValueError:
            return False

    def remove_alarm(self, name):
        with self._lock:
            for i, alarm in enumerate(self.alarms):
                if alarm.name.lower() == name.lower():
                    self.alarms.pop(i)
                    return True
        return False

    def list_alarms(self):
        with self._lock:
            return [{"name": a.name, "time": a.time_str, "active": a.enabled} for a in self.alarms if a.enabled]

    def start_monitoring(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _monitor(self):
        while self._running:
            with self._lock:
                alarms_copy = list(self.alarms)
            for alarm in alarms_copy:
                if alarm.should_trigger():
                    self._on_trigger(alarm.name)
            time.sleep(30)

    def _on_trigger(self, name):
        ringtone_manager.play_alarm()
        time.sleep(0.3)
        if self.tts:
            self.tts.speak(f"Alarm {name} is done!")

alarm_system = AlarmSystem()
