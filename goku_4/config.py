import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ALTERNATE MOTOR PINS - More reliable on Pi 5
# ALTERNATE PINS - More reliable on Pi 5
MOTOR_PINS = {
    'IN1': 5,     # Was 17
    'IN2': 6,     # Was 18 (user said this works)
    'IN3': 13,    # Was 22
    'IN4': 19,    # Was 23
    'ENA': 26,    # Was 27
    'ENB': 16,    # Was 25
}

CAMERA_INDEX = 20
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
DISPLAY_FPS = 60

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
GOOGLE_VISION_API_KEY = os.getenv('GOOGLE_VISION_API_KEY', '')
BLYNK_AUTH = os.getenv('BLYNK_AUTH', '')
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'goku220604@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', 'svbalaji2004@gmail.com')
ESP32_IP = os.getenv('ESP32_IP', '192.168.1.100')
ESP32_MAC = '00:70:07:26:0a:38'

MOTOR_SPEED = 70
TURN_SPEED = 60
SCAN_SPEED = 40

SPEECH_LANGUAGE = 'en-US'
TTS_RATE = 150
TTS_VOLUME = 1.0

ALERT_SUBJECT = "GOKU SECURITY ALERT"
ALERT_BODY = "Motion detected at perimeter. Investigating..."

ARDUINO_CLOUD_SECRET = "V6oCl#lryaejLM@VNLhclO@ND"

HOME_AUTOMATION = {
    'light_1': {'relay': 1, 'thing_id': '', 'property_id': '', 'name': 'Light 1'},
    'fan': {'relay': 2, 'thing_id': '', 'property_id': '', 'name': 'Fan'},
    'pump': {'relay': 3, 'thing_id': '', 'property_id': '', 'name': 'Pump Motor'},
    'ac': {'relay': 4, 'thing_id': '', 'property_id': '', 'name': 'Air Conditioner'},
    'light_2': {'relay': 5, 'thing_id': '', 'property_id': '', 'name': 'Light 2'},
}

AI_ROUTING = {
    'groq_models': ['llama-3.3-70b-versatile', 'llama-3.1-70b-versatile', 'mixtral-8x7b-32768'],
    'gemini_text_model': 'gemini-2.0-flash',
    'gemini_vision_model': 'gemini-2.5-flash',
    'default_model': 'gemini',
    'fallback_enabled': True,
}

BLUETOOTH_FOLLOW = {
    'target_mac': '',
}

COMMANDS = {
    'movement': ['forward', 'backward', 'stop', 'left', 'right', 'reverse'],
    'scan': ['scan', 'investigate', 'look around', 'sweep'],
    'home': ['light on', 'light off', 'lights on', 'lights off', 'fan on', 'fan off',
             'pump on', 'pump off', 'motor on', 'motor off', 'ac on', 'ac off',
             'air condition on', 'air condition off', 'all off', 'everything off'],
    'media': ['play', 'pause', 'stop', 'search for', 'who is', 'what is'],
}
