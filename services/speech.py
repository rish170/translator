import asyncio
import os
import tempfile
from pathlib import Path
import edge_tts
import ctypes
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from storage.settings import settings_manager

VOICE_MAPPING = {
    "en": "en-US-AriaNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "ja": "ja-JP-NanamiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "hi": "hi-IN-SwaraNeural",
    "ar": "ar-EG-SalmaNeural",
    "ru": "ru-RU-SvetlanaNeural"
}

class SpeechWorkerSignals(QObject):
    finished = pyqtSignal(str) # Path to the generated audio file
    error = pyqtSignal(str)

class SpeechWorker(QRunnable):
    def __init__(self, text, lang):
        super().__init__()
        self.text = text
        self.lang = lang
        self.signals = SpeechWorkerSignals()

    def run(self):
        try:
            # Map simple code to voice
            voice = VOICE_MAPPING.get(self.lang[:2].lower(), "en-US-AriaNeural")
            
            rate = settings_manager.get("speech_rate", "+0%")
            volume = settings_manager.get("speech_volume", "+0%")
            
            communicate = edge_tts.Communicate(self.text, voice, rate=rate, volume=volume)
            
            # Create a temporary file
            temp_dir = tempfile.gettempdir()
            output_file = os.path.join(temp_dir, f"translator_tts_{hash(self.text)}.mp3")
            
            # Run async function in a synchronous context
            asyncio.run(communicate.save(output_file))
            
            self.signals.finished.emit(output_file)
        except Exception as e:
            self.signals.error.emit(str(e))


class SpeechService(QObject):
    speech_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        
    def speak(self, text, lang):
        if not text.strip():
            return
            
        worker = SpeechWorker(text, lang)
        worker.signals.finished.connect(self._on_speech_ready)
        worker.signals.error.connect(self._on_speech_error)
        self.threadpool.start(worker)

    def _on_speech_ready(self, file_path):
        try:
            # Use Windows winmm to play the MP3 file without blocking
            alias = f"tts_{id(self)}"
            self.stop() # Stop any existing playback
            
            # Open the file
            cmd_open = f'open "{file_path}" alias {alias}'
            ctypes.windll.winmm.mciSendStringW(cmd_open, None, 0, None)
            
            # Play the file
            cmd_play = f'play {alias}'
            ctypes.windll.winmm.mciSendStringW(cmd_play, None, 0, None)
            
        except Exception as e:
            self.speech_error.emit(f"Playback Error: {e}")

    def _on_speech_error(self, error_msg):
        self.speech_error.emit(f"TTS Error: {error_msg}")

    def stop(self):
        try:
            alias = f"tts_{id(self)}"
            ctypes.windll.winmm.mciSendStringW(f'stop {alias}', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
        except Exception:
            pass

