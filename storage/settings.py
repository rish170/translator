import json
import os
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "config.json"

DEFAULT_SETTINGS = {
    "theme": "light",
    "font_size": 18,
    "speech_rate": "+0%",
    "speech_volume": "+0%",
    "auto_detect_language": False,
    "auto_translate_paste": True,
    "api_key": "",
    "api_region": "global",
    "window_geometry": None,
    "window_state": None,
    "pinned_languages": [],
    "recent_source_lang": "en",
    "recent_target_lang": "es"
}

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

# Global singleton
settings_manager = SettingsManager()
