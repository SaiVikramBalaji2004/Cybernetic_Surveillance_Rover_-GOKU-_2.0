import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ALTERNATE MOTOR PINS - More reliable on Pi 5
MOTOR_PINS = {
    'IN1': 5,    # Was 17 - Motor A +
    'IN2': 6,    # Was 18 - Motor A -
    'IN3': 13,   # Was 22 - Motor B +
    'IN4': 19,   # Was 23 - Motor B -
    'ENA': 26,   # Was 27 - Enable A (PWM)
    'ENB': 16,   # Was 25 - Enable B (PWM)
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

MOTOR_SPEED = 70
TURN_SPEED = 60
SCAN_SPEED = 40

SPEECH_LANGUAGE = 'en-US'
TTS_RATE = 150
TTS_VOLUME = 1.0

ALERT_SUBJECT = "GOKU SECURITY ALERT"
ALERT_BODY = "Motion detected at perimeter. Investigating..."

HOME_AUTOMATION = {
    'light_1': {'blynk_pin': 'V0', 'relay': 1, 'name': 'Living Room Light'},
    'light_2': {'blynk_pin': 'V1', 'relay': 2, 'name': 'Bedroom Light'},
    'fan': {'blynk_pin': 'V2', 'relay': 3, 'name': 'Ceiling Fan'},
    'ac': {'blynk_pin': 'V3', 'relay': 4, 'name': 'Air Conditioner'},
    'outlet_1': {'blynk_pin': 'V4', 'relay': 5, 'name': 'Power Outlet 1'},
    'outlet_2': {'blynk_pin': 'V5', 'relay': 6, 'name': 'Power Outlet 2'},
    'garage': {'blynk_pin': 'V6', 'relay': 7, 'name': 'Garage Door'},
    'gate': {'blynk_pin': 'V7', 'relay': 8, 'name': 'Main Gate'},
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
    'home': ['lights on', 'lights off', 'fan on', 'fan off', 'ac on', 'ac off'],
    'media': ['play', 'pause', 'stop', 'search for', 'who is', 'what is'],
}
