import uuid
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool
from services.cache import translation_cache
from storage.settings import settings_manager

class TranslatorWorkerSignals(QObject):
    finished = pyqtSignal(str, str, str, str)  # translated_text, source_text, source_lang, target_lang
    error = pyqtSignal(str)

class TranslatorWorker(QRunnable):
    def __init__(self, source_text, source_lang, target_lang, request_id):
        super().__init__()
        self.source_text = source_text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.request_id = request_id
        self.signals = TranslatorWorkerSignals()
        self.is_cancelled = False

    def run(self):
        if self.is_cancelled:
            return

        # 1. Check Char limit (e.g., 50000 limit for some tiers, but we'll soft limit at 10000 to be safe)
        if len(self.source_text) > 10000:
            self.signals.error.emit("Character limit exceeded (10,000 max).")
            return

        # 2. Check cache
        cached_result = translation_cache.get(self.source_text, self.source_lang, self.target_lang)
        if cached_result:
            if not self.is_cancelled:
                self.signals.finished.emit(cached_result, self.source_text, self.source_lang, self.target_lang)
            return

        # 3. Call Microsoft Translator API
        api_key = settings_manager.get("api_key")
        api_region = settings_manager.get("api_region")

        if not api_key:
            self.signals.error.emit("API Key is missing. Please set it in Settings.")
            return

        endpoint = "https://api.cognitive.microsofttranslator.com/translate"
        params = {
            'api-version': '3.0',
            'to': self.target_lang
        }
        if self.source_lang and self.source_lang != "detect":
            params['from'] = self.source_lang

        headers = {
            'Ocp-Apim-Subscription-Key': api_key,
            'Ocp-Apim-Subscription-Region': api_region,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }

        body = [{'text': self.source_text}]

        try:
            response = requests.post(endpoint, params=params, headers=headers, json=body, timeout=5)
            response.raise_for_status()
            result = response.json()
            
            if self.is_cancelled:
                return

            translated_text = result[0]['translations'][0]['text']
            
            # Save to cache
            translation_cache.set(self.source_text, self.source_lang, self.target_lang, translated_text)
            
            self.signals.finished.emit(translated_text, self.source_text, self.source_lang, self.target_lang)

        except requests.exceptions.RequestException as e:
            if not self.is_cancelled:
                if hasattr(e, 'response') and e.response is not None:
                    # Try to extract detailed Azure API error message
                    try:
                        err_json = e.response.json()
                        error_msg = err_json.get('error', {}).get('message', str(e))
                        self.signals.error.emit(f"API Error: {error_msg}")
                    except Exception:
                        self.signals.error.emit(f"Network Error: {e}")
                else:
                    self.signals.error.emit(f"Network Error: {e}")


class TranslatorService(QObject):
    translation_finished = pyqtSignal(str, str, str, str)
    translation_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        self.current_worker = None

    def translate(self, text, source_lang, target_lang):
        if not text.strip():
            self.translation_finished.emit("", "", source_lang, target_lang)
            return

        # Cancel previous request
        if self.current_worker:
            self.current_worker.is_cancelled = True

        request_id = str(uuid.uuid4())
        worker = TranslatorWorker(text, source_lang, target_lang, request_id)
        
        # Connect signals
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)

        self.current_worker = worker
        self.threadpool.start(worker)

    def _on_finished(self, translated_text, source_text, source_lang, target_lang):
        self.translation_finished.emit(translated_text, source_text, source_lang, target_lang)

    def _on_error(self, error_msg):
        self.translation_error.emit(error_msg)
