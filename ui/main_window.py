import sys
import os
import socket
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QToolButton, QFrame, QSplitter, QApplication, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QGuiApplication

from ui.components import SearchableComboBox, ToastNotification, LoadingIndicator, LiveStatistics
from ui.settings_dialog import SettingsDialog
from ui.history_panel import HistoryPanel
from services.translator import TranslatorService
from services.speech import SpeechService
from storage.settings import settings_manager
from storage.history import history_manager

class InternetMonitor(QThread):
    status_changed = pyqtSignal(bool)
    
    def run(self):
        while True:
            try:
                socket.create_connection(("1.1.1.1", 53), timeout=3)
                self.status_changed.emit(True)
            except OSError:
                self.status_changed.emit(False)
            self.sleep(3)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal Translator")
        self.setMinimumSize(1000, 650)
        
        # Init Services
        self.translator = TranslatorService()
        self.translator.translation_finished.connect(self.on_translation_finished)
        self.translator.translation_error.connect(self.on_translation_error)
        
        self.speech = SpeechService()
        self.speech.speech_error.connect(self.on_speech_error)
        
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.trigger_translation)
        
        self.internet_monitor = InternetMonitor()
        self.internet_monitor.status_changed.connect(self.update_internet_status)
        self.has_internet = True
        self.internet_monitor.start()

        self.setup_ui()
        self.load_state()

    def get_icon_path(self, icon_name):
        return str(Path(__file__).parent.parent / "assets" / "icons" / icon_name)

    def create_tool_button(self, icon_name, tooltip, callback=None):
        btn = QToolButton()
        btn.setIcon(QIcon(self.get_icon_path(icon_name)))
        btn.setIconSize(QSize(20, 20))
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if callback:
            btn.clicked.connect(callback)
        return btn

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 30)
        
        # Top Bar
        top_bar = QHBoxLayout()
        self.internet_status_label = QLabel("● Connected")
        self.internet_status_label.setStyleSheet("color: #107C10; font-weight: bold;")
        top_bar.addWidget(self.internet_status_label)
        
        top_bar.addStretch()
        
        self.history_btn = self.create_tool_button("history.svg", "History", self.toggle_history)
        self.settings_btn = self.create_tool_button("settings.svg", "Settings", self.open_settings)
        self.theme_btn = self.create_tool_button("moon.svg", "Toggle Theme", self.toggle_theme)
        
        top_bar.addWidget(self.history_btn)
        top_bar.addWidget(self.settings_btn)
        top_bar.addWidget(self.theme_btn)
        
        main_layout.addLayout(top_bar)
        
        # Splitter for panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Panel (Source)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0,0,0,0)
        
        self.source_lang_combo = SearchableComboBox()
        self.source_lang_combo.addItems(["en - English", "es - Spanish", "fr - French", "de - German", "it - Italian", "ja - Japanese", "zh - Chinese", "hi - Hindi"])
        left_layout.addWidget(self.source_lang_combo)
        
        self.source_text = QTextEdit()
        self.source_text.setPlaceholderText("Enter text to translate...")
        self.source_text.textChanged.connect(self.on_source_text_changed)
        left_layout.addWidget(self.source_text)
        
        left_bottom = QHBoxLayout()
        self.live_stats = LiveStatistics()
        left_bottom.addWidget(self.live_stats)
        left_bottom.addStretch()
        self.clear_btn = self.create_tool_button("clear.svg", "Clear", self.clear_text)
        self.source_speak_btn = self.create_tool_button("speak.svg", "Speak Source", self.speak_source)
        self.source_copy_btn = self.create_tool_button("copy.svg", "Copy Source", self.copy_source)
        left_bottom.addWidget(self.clear_btn)
        left_bottom.addWidget(self.source_speak_btn)
        left_bottom.addWidget(self.source_copy_btn)
        left_layout.addLayout(left_bottom)
        
        # Middle (Swap)
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.swap_btn = self.create_tool_button("swap.svg", "Swap Languages")
        self.swap_btn.setObjectName("swapButton")
        self.swap_btn.setIconSize(QSize(24, 24))
        self.swap_btn.clicked.connect(self.swap_languages)
        middle_layout.addWidget(self.swap_btn)
        
        # Right Panel (Target)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0,0,0,0)
        
        self.target_lang_combo = SearchableComboBox()
        self.target_lang_combo.addItems(["en - English", "es - Spanish", "fr - French", "de - German", "it - Italian", "ja - Japanese", "zh - Chinese", "hi - Hindi"])
        self.target_lang_combo.currentTextChanged.connect(self.on_target_lang_changed)
        right_layout.addWidget(self.target_lang_combo)
        
        self.target_text = QTextEdit()
        self.target_text.setReadOnly(True)
        right_layout.addWidget(self.target_text)
        
        right_bottom = QHBoxLayout()
        self.loading_indicator = LoadingIndicator()
        right_bottom.addWidget(self.loading_indicator)
        right_bottom.addStretch()
        
        self.star_btn = self.create_tool_button("star_outline.svg", "Favorite", self.toggle_favorite)
        self.target_speak_btn = self.create_tool_button("speak.svg", "Speak Translated", self.speak_target)
        self.target_copy_btn = self.create_tool_button("copy.svg", "Copy Translated", self.copy_target)
        right_bottom.addWidget(self.star_btn)
        right_bottom.addWidget(self.target_speak_btn)
        right_bottom.addWidget(self.target_copy_btn)
        right_layout.addLayout(right_bottom)
        
        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(middle_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setSizes([450, 50, 450])
        
        main_layout.addWidget(self.splitter)
        
        self.history_panel = HistoryPanel()
        self.history_panel.hide()

    def update_internet_status(self, has_internet):
        self.has_internet = has_internet
        if has_internet:
            self.internet_status_label.setText("● Connected")
            self.internet_status_label.setStyleSheet("color: #107C10; font-weight: bold;")
        else:
            self.internet_status_label.setText("● No Internet Connection")
            self.internet_status_label.setStyleSheet("color: #D13438; font-weight: bold;")

    def on_source_text_changed(self):
        text = self.source_text.toPlainText()
        self.live_stats.update_stats(text)
        
        if not text.strip():
            self.target_text.clear()
            return
            
        self.debounce_timer.start(400) # 400ms debounce
        
    def trigger_translation(self):
        if not self.has_internet:
            ToastNotification(self, "No internet connection. Translation paused.").show_toast()
            return
            
        text = self.source_text.toPlainText().strip()
        if not text:
            return
            
        source_lang = self.source_lang_combo.currentText().split(' - ')[0]
        target_lang = self.target_lang_combo.currentText().split(' - ')[0]
        
        self.loading_indicator.start()
        self.translator.translate(text, source_lang, target_lang)
        
    def on_translation_finished(self, translated_text, source_text, source_lang, target_lang):
        self.loading_indicator.stop()
        self.target_text.setText(translated_text)
        history_manager.add_translation(source_text, translated_text, source_lang, target_lang)
        self.history_panel.load_history()
        
    def on_translation_error(self, error_msg):
        self.loading_indicator.stop()
        ToastNotification(self, error_msg).show_toast()
        
    def on_target_lang_changed(self):
        self.trigger_translation()
        
    def swap_languages(self):
        src_idx = self.source_lang_combo.currentIndex()
        tgt_idx = self.target_lang_combo.currentIndex()
        
        self.source_lang_combo.setCurrentIndex(tgt_idx)
        self.target_lang_combo.setCurrentIndex(src_idx)
        
        src_text = self.source_text.toPlainText()
        tgt_text = self.target_text.toPlainText()
        
        self.source_text.blockSignals(True)
        self.source_text.setText(tgt_text)
        self.source_text.blockSignals(False)
        
        # Trigger retranslation for the new swapped text
        self.trigger_translation()

    def clear_text(self):
        self.source_text.clear()
        self.target_text.clear()

    def copy_source(self):
        QGuiApplication.clipboard().setText(self.source_text.toPlainText())
        ToastNotification(self, "Copied Source!").show_toast()

    def copy_target(self):
        QGuiApplication.clipboard().setText(self.target_text.toPlainText())
        ToastNotification(self, "Copied Translated!").show_toast()
        
    def speak_source(self):
        text = self.source_text.toPlainText()
        lang = self.source_lang_combo.currentText().split(' - ')[0]
        self.speech.speak(text, lang)

    def speak_target(self):
        text = self.target_text.toPlainText()
        lang = self.target_lang_combo.currentText().split(' - ')[0]
        self.speech.speak(text, lang)
        
    def on_speech_error(self, msg):
        ToastNotification(self, msg).show_toast()

    def toggle_favorite(self):
        ToastNotification(self, "Added to Favorites!").show_toast()
        
    def toggle_history(self):
        if self.history_panel.isVisible():
            self.history_panel.hide()
        else:
            self.history_panel.show()
            self.history_panel.raise_()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
        
    def toggle_theme(self):
        current_theme = settings_manager.get("theme", "light")
        new_theme = "dark" if current_theme == "light" else "light"
        settings_manager.set("theme", new_theme)
        self.apply_theme()
        
    def update_icon_colors(self, theme):
        import re
        color = "#FFFFFF" if theme == "dark" else "#606060"
        icons_dir = Path(__file__).parent.parent / "assets" / "icons"
        for svg_file in icons_dir.glob("*.svg"):
            with open(svg_file, "r", encoding="utf-8") as f:
                content = f.read()
            content = re.sub(r'stroke="(#[A-Fa-f0-9]{6}|currentColor)"', f'stroke="{color}"', content)
            # Be careful with fill="none", we only want to replace currentColor or hex
            content = re.sub(r'fill="(#[A-Fa-f0-9]{6}|currentColor)"', f'fill="{color}"', content)
            with open(svg_file, "w", encoding="utf-8") as f:
                f.write(content)

    def refresh_icons(self):
        theme = settings_manager.get("theme", "light")
        self.update_icon_colors(theme)
        
        self.history_btn.setIcon(QIcon(self.get_icon_path("history.svg")))
        self.settings_btn.setIcon(QIcon(self.get_icon_path("settings.svg")))
        self.theme_btn.setIcon(QIcon(self.get_icon_path("sun.svg" if theme == "dark" else "moon.svg")))
        self.swap_btn.setIcon(QIcon(self.get_icon_path("swap.svg")))
        self.clear_btn.setIcon(QIcon(self.get_icon_path("clear.svg")))
        self.source_speak_btn.setIcon(QIcon(self.get_icon_path("speak.svg")))
        self.source_copy_btn.setIcon(QIcon(self.get_icon_path("copy.svg")))
        self.star_btn.setIcon(QIcon(self.get_icon_path("star_outline.svg")))
        self.target_speak_btn.setIcon(QIcon(self.get_icon_path("speak.svg")))
        self.target_copy_btn.setIcon(QIcon(self.get_icon_path("copy.svg")))

    def apply_theme(self):
        theme = settings_manager.get("theme", "light")
        self.refresh_icons()
        
        style_path = Path(__file__).parent.parent / "styles" / f"{theme}.qss"
        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                qss = f.read()
            
            arrow_path = str(Path(__file__).parent.parent / "assets" / "icons" / "down_arrow.svg").replace('\\', '/')
            qss = qss.replace("{ARROW_PATH}", arrow_path)
            
            QApplication.instance().setStyleSheet(qss)
                
    def load_state(self):
        # Load theme
        self.apply_theme()
        
        # Load previous languages
        src_lang = settings_manager.get("recent_source_lang", "en")
        tgt_lang = settings_manager.get("recent_target_lang", "es")
        
        for i in range(self.source_lang_combo.count()):
            if self.source_lang_combo.itemText(i).startswith(src_lang):
                self.source_lang_combo.setCurrentIndex(i)
                break
                
        for i in range(self.target_lang_combo.count()):
            if self.target_lang_combo.itemText(i).startswith(tgt_lang):
                self.target_lang_combo.setCurrentIndex(i)
                break
                
        geom = settings_manager.get("window_geometry")
        if geom:
            # Simple restore for this implementation
            pass
            
    def closeEvent(self, event):
        settings_manager.set("recent_source_lang", self.source_lang_combo.currentText().split(' - ')[0])
        settings_manager.set("recent_target_lang", self.target_lang_combo.currentText().split(' - ')[0])
        event.accept()
