import sys
import os
import signal
import logging

# Add venv packages to path
script_dir = os.path.dirname(os.path.abspath(__file__))
venv_lib = os.path.join(script_dir, "venv", "lib", "python3.13", "site-packages")
if os.path.isdir(venv_lib):
    sys.path.insert(0, venv_lib)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
os.environ["SDL_AUDIODRIVER"] = "alsa"

from rover_controller import rover_controller

def signal_handler(sig, frame):
    print("\nShutdown signal received.")
    rover_controller.shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    try:
        rover_controller.initialize()
        rover_controller.start()
    except KeyboardInterrupt:
        pass
    finally:
        rover_controller.shutdown()
