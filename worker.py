import os
import sys
import time
import json
import ctypes

# ----------------------------
# Prevent multiple instances (Windows Mutex)
# ----------------------------
mutex = ctypes.windll.kernel32.CreateMutexW(
    None, False, "Global\\HealthActivityTimerWorker"
)

if ctypes.windll.kernel32.GetLastError() == 183:
    sys.exit(0)

# ----------------------------
# Hide pygame console message
# ----------------------------
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


# ----------------------------
# Base directory (works for .py and .exe)
# ----------------------------
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")


# ----------------------------
# Load settings safely
# ----------------------------
def load_settings():
    if not os.path.exists(CONFIG_FILE):
        return {"interval": 20, "sound_path": "./Default.mp3", "enabled": False}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, Exception):
        return {"interval": 20, "sound_path": "./Default.mp3", "enabled": True}


# ----------------------------
# Audio system init (once)
# ----------------------------
try:
    pygame.mixer.init()
except:
    pass


def play_alarm(sound_path):
    """Play alarm sound or fallback beep"""
    full_path = os.path.join(BASE_DIR, sound_path)

    try:
        if not os.path.exists(full_path):
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return

        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play()

        timeout = 0
        while pygame.mixer.music.get_busy() and timeout < 15:
            time.sleep(1)
            timeout += 1

    except Exception:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)


# ----------------------------
# Main loop
# ----------------------------
def main():
    while True:
        settings = load_settings()

        # Exit if disabled
        if not settings.get("enabled", False):
            sys.exit(0)

        # Read interval (minutes → seconds)
        try:
            interval_minutes = int(settings.get("interval", 20))
        except ValueError:
            interval_minutes = 20

        interval_seconds = interval_minutes * 60

        # Sleep
        time.sleep(interval_seconds)

        # Re-check before playing alarm (important safety check)
        settings = load_settings()

        if settings.get("enabled", False):
            play_alarm(settings.get("sound_path", "./Default.mp3"))


# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    main()