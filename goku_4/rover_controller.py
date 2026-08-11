import time
import logging
import threading
import re
from typing import Optional
from motor_control import motor_controller
from camera_stream import camera_stream
from display_controller import display_controller
from speech_handler import speech_recognition
from tts_engine import tts_engine
from ai_router import ai_router
from home_automation import home_automation
from media_control import media_control
from email_notifier import email_notifier
from alarm_system import alarm_system
from timer_system import timer_system
from navigation import navigation_system, Direction, TrajectoryState
from bluetooth_follower import init_follower, bluetooth_follower
from keypad_controller import KeypadController

logger = logging.getLogger('GOKU.Rover')

class RoverController:
    def __init__(self):
        self.running = False
        self.autonomous_mode = False
        self.keypad = None

    def initialize(self):
        logger.info("Initializing GOKU systems...")

        display_controller.initialize()
        display_controller.set_status("Initializing...")

        try:
            motor_ok = motor_controller.initialize()
            logger.info(f"Motor init result: {motor_ok}, initialized={motor_controller.initialized}")
        except Exception as e:
            logger.warning(f"Motor init: {e}")

        self.keypad = KeypadController(motor_controller)

        camera_stream.initialize()
        speech_recognition.initialize()
        tts_engine.initialize()

        ai_router.groq.initialize()
        gemini_ok = ai_router.gemini.initialize()
        if not gemini_ok:
            logger.info("Gemini unavailable, Groq is primary")
        ai_router.vision.initialize()
        ai_router.weather.initialize()
        ai_router.media.initialize()
        init_follower(motor_controller)

        home_automation.initialize()
        email_notifier.initialize()

        alarm_system.initialize(tts=tts_engine)
        alarm_system.start_monitoring()

        timer_system.initialize(tts=tts_engine)

        display_controller.set_status("GOKU Online")
        logger.info("All systems initialized")
        return True

    def start(self):
        self.running = True
        camera_stream.start()

        if self.keypad:
            self.keypad.start()

        print("\n" + "="*50)
        print("GOKU ROVER READY")
        print("Voice: Speak commands naturally")
        print("Keys:  W=Forward  A=Left  S=Backward  D=Right  Space=Stop")
        print("       Q=Exit keypad mode  Ctrl+C=Shutdown")
        print("="*50 + "\n")

        tts_engine.speak("Goku online. All systems ready.")
        display_controller.set_status("Ready")

        self.command_loop()

    def command_loop(self):
        logger.info("Entering command loop")

        while self.running:
            display_controller.update()
            display_controller.set_status("Listening...")
            display_controller.set_expression('listening')

            command = speech_recognition.listen_once(timeout=4)

            if command:
                display_controller.set_status(f"Processing: {command}")
                self.process_command(command)

            time.sleep(0.1)

    def process_command(self, command):
        cl = command.lower().strip()
        logger.info(f"Command received: {command}")

        if cl in ('stop', 'stop now', 'stop moving', 'halt'):
            motor_controller.stop()
            self.autonomous_mode = False
            if bluetooth_follower and bluetooth_follower.is_following():
                bluetooth_follower.stop_following()
            display_controller.set_status("Stopped")
            tts_engine.speak("Stopped")
            return

        if cl in ('stop follow', 'stop following', 'stop tracking'):
            if bluetooth_follower and bluetooth_follower.is_following():
                bluetooth_follower.stop_following()
                display_controller.set_status("Follow Stopped")
                tts_engine.speak("Following stopped")
            else:
                tts_engine.speak("Not following anything")
            return

        if cl in ('autonomous mode', 'auto mode', 'enable autonomous', 'start autonomous'):
            self.autonomous_mode = True
            display_controller.set_status("Autonomous Mode Active")
            tts_engine.speak("Autonomous mode enabled")
            return

        if cl in ('manual mode', 'disable autonomous', 'stop autonomous', 'exit autonomous'):
            self.autonomous_mode = False
            display_controller.set_status("Manual Mode")
            tts_engine.speak("Autonomous mode disabled")
            return

        if cl in ('navigate forward', 'auto navigate', 'go autonomous'):
            self.autonomous_mode = True
            display_controller.set_status("Autonomous Navigation")
            tts_engine.speak("Starting autonomous navigation")
            self._autonomous_navigation_loop()
            return

        route = ai_router.route(command)
        logger.info(f"Command route: {route}")

        if route['type'] == 'movement':
            self.handle_movement(command)
        elif route['type'] == 'home_control':
            self.handle_home_control(command)
        elif route['type'] == 'save_mac':
            self.handle_save_mac(command)
        elif route['type'] == 'follow':
            self.handle_follow(command)
        elif route['type'] == 'scan':
            self.handle_scan(command)
        else:
            self.handle_ai_query(command)

    def handle_alarm_action(self, action_type, **kwargs):
        if action_type == 'list':
            alarms = alarm_system.list_alarms()
            if alarms:
                parts = [f"{a['name']} at {a['time']}" for a in alarms]
                tts_engine.speak("Active alarms: " + ", ".join(parts))
            else:
                tts_engine.speak("No alarms set")

        elif action_type == 'delete':
            name = kwargs.get('name', '')
            for alarm in alarm_system.list_alarms():
                if alarm['name'].lower() in name:
                    alarm_system.remove_alarm(alarm['name'])
                    tts_engine.speak(f"Alarm {alarm['name']} removed")
                    return
            tts_engine.speak("Alarm not found")

        elif action_type == 'set':
            time_str = kwargs.get('time_str')
            name = kwargs.get('name', 'default')
            if time_str:
                alarm_system.add_alarm(name, time_str)
                alarm_system.start_monitoring()
                h, mi = time_str.split(':')
                hi = int(h)
                ampm = "AM" if hi < 12 else "PM"
                dh = hi if hi <= 12 else hi - 12
                if dh == 0:
                    dh = 12
                tts_engine.speak(f"Alarm {name} set for {dh}:{mi} {ampm}")
            else:
                tts_engine.speak("Please specify a time for the alarm")

    def handle_timer_action(self, action_type, **kwargs):
        if action_type == 'list':
            timers = timer_system.list_timers()
            if timers:
                parts = []
                for n, info in timers.items():
                    mins = int(info['remaining'] / 60)
                    secs = int(info['remaining'] % 60)
                    if mins > 0:
                        parts.append(f"{n} with {mins} minutes {secs} seconds left")
                    else:
                        parts.append(f"{n} with {secs} seconds left")
                tts_engine.speak("Active timers: " + ", ".join(parts))
            else:
                tts_engine.speak("No timers set")

        elif action_type == 'stop':
            name = kwargs.get('name', '')
            for n in timer_system.list_timers():
                if n.lower() in name:
                    timer_system.stop_timer(n)
                    tts_engine.speak(f"Timer {n} stopped")
                    return
            tts_engine.speak("Timer not found")

        elif action_type == 'set':
            duration = kwargs.get('duration')
            name = kwargs.get('name', 'default')
            if duration:
                timer_system.create_timer(name, duration)
                timer_system.start_timer(name)
                mins = int(duration / 60)
                secs = int(duration % 60)
                if mins > 0:
                    tts_engine.speak(f"Timer {name} set for {mins} minutes and {secs} seconds")
                else:
                    tts_engine.speak(f"Timer {name} set for {secs} seconds")
            else:
                tts_engine.speak("Please specify a duration for the timer")

    def handle_movement(self, command):
        display_controller.set_expression('neutral')
        cl = command.lower()
        logger.info(f"Movement command received: {command}, motor_initialized={motor_controller.initialized}")
        if not motor_controller.initialized:
            tts_engine.speak("Motors not ready")
            logger.error("Motor not initialized, cannot move")
            return

        direction = None
        duration = 2.0

        if 'forward' in cl:
            direction = Direction.FORWARD
            m = re.search(r'(\d+)\s*seconds?', cl)
            if m:
                duration = int(m.group(1))
        elif 'backward' in cl or 'back' in cl:
            direction = Direction.BACKWARD
            m = re.search(r'(\d+)\s*seconds?', cl)
            if m:
                duration = int(m.group(1))
        elif 'left' in cl:
            direction = Direction.LEFT
        elif 'right' in cl:
            direction = Direction.RIGHT
        else:
            logger.warning(f"No movement matched for: {command}")
            return

        trajectory = navigation_system.plan_directional_movement(direction.value, duration)
        tts_engine.speak(f"Moving {direction.value}")
        display_controller.set_status(f"Moving {direction.value}")

        def tts_cb(msg):
            tts_engine.speak(msg)

        def display_cb(status, expr):
            display_controller.set_status(status)
            display_controller.set_expression(expr)

        state = navigation_system.move_with_avoidance(
            motor_controller, direction, duration,
            tts_callback=tts_cb,
            display_callback=display_cb
        )

        if state == TrajectoryState.DESTINATION_REACHED:
            tts_engine.speak("Movement complete")
        elif state == TrajectoryState.BLOCKED:
            tts_engine.speak("Path blocked")

        display_controller.set_status("Ready")
        display_controller.set_expression('neutral')

    def handle_home_control(self, command):
        result = home_automation.process_command(command)
        if result:
            tts_engine.speak(result)
        else:
            tts_engine.speak("Command not recognized")

    def handle_scan(self, command):
        display_controller.set_expression('scanning')
        tts_engine.speak("Scanning perimeter")
        try:
            for _ in range(3):
                motor_controller.scan_left()
                time.sleep(1)
                motor_controller.scan_right()
                time.sleep(1)
            motor_controller.stop()
        except:
            pass
        display_controller.set_expression('neutral')
        tts_engine.speak("Scan complete. All clear.")
        display_controller.set_status("Ready")

    def handle_follow(self, command):
        cl = command.lower().strip()
        display_controller.set_expression('scanning')
        display_controller.set_status("Follow Mode")

        if not bluetooth_follower:
            tts_engine.speak("Bluetooth follow not available")
            return

        if bluetooth_follower.is_following():
            bluetooth_follower.stop_following()
            tts_engine.speak("Following stopped")
            return

        mac = bluetooth_follower.parse_mac_from_command(command)

        if mac:
            bluetooth_follower.set_target(mac)
            tts_engine.speak(f"Following device {mac}")
            display_controller.set_status(f"Following: {mac}")
        else:
            tts_engine.speak("Scanning for your device. Please keep Bluetooth on.")
            time.sleep(2)

            devices = self._scan_nearby_devices()
            if devices:
                device = devices[0]
                bluetooth_follower.set_target(device['mac'])
                tts_engine.speak(f"Following {device.get('name', 'your device')}")
                display_controller.set_status(f"Following: {device['mac']}")
            else:
                display_controller.set_expression('neutral')
                display_controller.set_status("Ready")
                tts_engine.speak("No devices found. Please provide the Bluetooth MAC address.")
                return

        def tts_cb(msg):
            tts_engine.speak(msg)

        def display_cb(status, expr):
            display_controller.set_status(status)
            display_controller.set_expression(expr)

        ok = bluetooth_follower.start_following(tts_callback=tts_cb, display_callback=display_cb)
        if ok:
            tts_engine.speak("Following started. Say stop to end.")

    def _scan_nearby_devices(self):
        import subprocess
        try:
            proc = subprocess.run(
                ['bluetoothctl', '--timeout', '10', 'scan', 'on'],
                capture_output=True, text=True, timeout=12
            )
            proc = subprocess.run(
                ['bluetoothctl', 'devices'],
                capture_output=True, text=True, timeout=5
            )
            devices = []
            for line in proc.stdout.strip().split('\n'):
                m = re.match(r'Device\s+([0-9A-F:]{17})\s+(.*)', line, re.IGNORECASE)
                if m:
                    devices.append({'mac': m.group(1), 'name': m.group(2).strip()})
            return devices
        except Exception as e:
            logger.warning(f"Bluetooth scan failed: {e}")
            return []

    def handle_save_mac(self, command):
        if not bluetooth_follower:
            tts_engine.speak("Bluetooth follow not available")
            return

        mac = bluetooth_follower.parse_mac_from_command(command)
        if mac:
            bluetooth_follower.set_target(mac)
            tts_engine.speak(f"Device {mac} saved as your target")
            display_controller.set_status(f"Target Saved: {mac}")
        else:
            saved = bluetooth_follower.get_saved_mac()
            if saved:
                tts_engine.speak(f"Your saved device is {saved}")
            else:
                tts_engine.speak("No MAC address found. Say: save my device followed by the MAC address.")

    def handle_ai_query(self, command):
        display_controller.set_expression('speaking')
        display_controller.set_status("Thinking...")

        try:
            image_bytes = camera_stream.capture_frame_as_bytes()
            if image_bytes:
                logger.info(f"Camera captured {len(image_bytes)} bytes for query")
            else:
                logger.warning("Camera returned no image data")

            response = ai_router.ask(command, image_bytes=image_bytes)

            if response is None:
                tts_engine.speak("Unable to answer right now. Please try again.")
                return

            if isinstance(response, dict):
                response_type = response.get('type')

                if response_type == 'alarm':
                    self._handle_alarm_via_ai(response['command'])
                elif response_type == 'timer':
                    self._handle_timer_via_ai(response['command'])
                elif response_type == 'movement':
                    self.handle_movement(response['command'])
                elif response_type == 'home_control':
                    self.handle_home_control(response['command'])
                elif response_type == 'follow':
                    self.handle_follow(response['command'])
                else:
                    tts_engine.speak("I heard you but could not process that.")
                return

            if isinstance(response, str):
                response = ' '.join(response.split())
                logger.info(f"AI response: {response}")
                tts_engine.speak(response)
                return

            tts_engine.speak("Unable to answer right now. Please try again.")
        except Exception as e:
            logger.error(f"AI query error: {e}", exc_info=True)
            tts_engine.speak("Unable to answer right now. Please try again.")

        display_controller.set_expression('neutral')
        display_controller.set_status("Ready")

    def _handle_alarm_via_ai(self, command):
        cl = command.lower()

        if 'list' in cl or 'show' in cl:
            self.handle_alarm_action('list')
        elif 'delete' in cl or 'remove' in cl or 'cancel' in cl:
            found = False
            for alarm in alarm_system.list_alarms():
                if alarm['name'].lower() in cl:
                    alarm_system.remove_alarm(alarm['name'])
                    tts_engine.speak(f"Alarm {alarm['name']} removed")
                    found = True
                    break
            if not found:
                tts_engine.speak("Alarm not found")
        elif 'set' in cl or 'create' in cl:
            time_str = self._parse_time(command)
            name = self._extract_name(command)
            self.handle_alarm_action('set', time_str=time_str, name=name)
        else:
            tts_engine.speak("I didn't understand the alarm command")

    def _handle_timer_via_ai(self, command):
        cl = command.lower()

        if 'list' in cl or 'show' in cl:
            self.handle_timer_action('list')
        elif 'stop' in cl or 'cancel' in cl:
            name = cl
            self.handle_timer_action('stop', name=name)
        elif 'pause' in cl:
            for name in timer_system.list_timers():
                if name.lower() in cl:
                    timer_system.pause_timer(name)
                    tts_engine.speak(f"Timer {name} paused")
                    return
            tts_engine.speak("Timer not found")
        elif 'resume' in cl:
            for name in timer_system.list_timers():
                if name.lower() in cl:
                    timer_system.resume_timer(name)
                    tts_engine.speak(f"Timer {name} resumed")
                    return
            tts_engine.speak("Timer not found")
        elif any(w in cl for w in ['set', 'create', 'start', 'remind me']):
            duration = self._parse_duration(cl)
            name = self._extract_name(command)
            self.handle_timer_action('set', duration=duration, name=name)
        else:
            tts_engine.speak("I didn't understand the timer command")

    def _parse_time(self, command):
        m = re.search(r'(\d{1,2})[:\.](\d{2})', command)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return f"{h:02d}:{mi:02d}"
        m = re.search(r'\bat\s+(\d{1,2})\s+(\d{2})\b', command)
        if m:
            h, mi = int(m.group(1)), int(m.group(2))
            if 0 <= h <= 23 and 0 <= mi <= 59:
                return f"{h:02d}:{mi:02d}"
        return None

    def _parse_duration(self, command):
        cl = command.lower()
        spoken = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,
                  'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,
                  'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,
                  'seventeen':17,'eighteen':18,'nineteen':19,'twenty':20,
                  'thirty':30,'forty':40,'fifty':50,'sixty':60,
                  'seventy':70,'eighty':80,'ninety':90,
                  'hundred':100}
        for word, val in spoken.items():
            cl = cl.replace(f'{word} minute', f'{val} minute')
            cl = cl.replace(f'{word} minutes', f'{val} minutes')
            cl = cl.replace(f'{word} second', f'{val} second')
            cl = cl.replace(f'{word} seconds', f'{val} seconds')
            cl = cl.replace(f'{word} hour', f'{val} hour')
            cl = cl.replace(f'{word} hours', f'{val} hours')

        cl = cl.replace('half hour', '30 minutes')
        cl = cl.replace('half minute', '30 seconds')
        cl = cl.replace('quarter hour', '15 minutes')
        cl = cl.replace('quarter of an hour', '15 minutes')
        cl = cl.replace('an hour', '1 hour')
        cl = cl.replace('a minute', '1 minute')
        cl = cl.replace('a second', '1 second')
        cl = cl.replace('a few minutes', '3 minutes')
        cl = cl.replace('a few seconds', '5 seconds')
        cl = cl.replace('a moment', '10 seconds')

        total = 0
        for pat, mult in [(r'(\d+)\s*(?:hours?|hrs?)\b', 3600),
                          (r'(\d+)\s*(?:minutes?|mins?)\b', 60),
                          (r'(\d+)\s*(?:seconds?|secs?)\b', 1)]:
            m = re.search(pat, cl)
            if m:
                total += int(m.group(1)) * mult

        if total == 0:
            m = re.search(r'(\d+)', cl)
            if m:
                val = int(m.group(1))
                if 'hour' in cl:
                    total = val * 3600
                elif 'minute' in cl or 'min' in cl:
                    total = val * 60
                elif 'second' in cl or 'sec' in cl:
                    total = val
                elif val <= 60:
                    total = val

        if total > 540000:
            return None

        return total if total > 0 else None

    def _extract_name(self, command):
        cl = command.lower()
        for kw in ['called ', 'named ']:
            if kw in cl:
                name = cl.split(kw, 1)[1].strip().rstrip('?')
                if name:
                    return name
        return "default"

    def _autonomous_navigation_loop(self):
        tts_engine.speak("Navigating autonomously")
        nav_thread = threading.Thread(target=self._run_autonomous_navigation)
        nav_thread.daemon = True
        nav_thread.start()

    def _run_autonomous_navigation(self):
        def tts_cb(msg):
            tts_engine.speak(msg)

        def display_cb(status, expr):
            display_controller.set_status(status)
            display_controller.set_expression(expr)

        state = navigation_system.autonomous_navigate(
            motor_controller, duration=30.0,
            tts_callback=tts_cb,
            display_callback=display_cb
        )

        motor_controller.stop()
        self.autonomous_mode = False
        display_controller.set_status("Ready")
        if state == TrajectoryState.DESTINATION_REACHED:
            tts_engine.speak("Autonomous navigation complete")
        else:
            tts_engine.speak("Navigation stopped")

    def shutdown(self):
        self.running = False
        self.autonomous_mode = False
        if self.keypad:
            self.keypad.stop()
        motor_controller.stop()
        media_control.stop()
        if bluetooth_follower and bluetooth_follower.is_following():
            bluetooth_follower.stop_following()
        try:
            motor_controller.cleanup()
        except:
            pass
        camera_stream.stop()
        display_controller.cleanup()
        alarm_system.stop_monitoring()
        timer_system.stop_all()
        logger.info("GOKU shutdown complete")

rover_controller = RoverController()
