from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QFormLayout
)
from storage.settings import settings_manager
from ui.components import ToggleSwitch

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # API Key (Masked)
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setText(settings_manager.get("api_key", ""))
        form_layout.addRow("API Key:", self.api_key_input)
        
        # API Region
        self.api_region_input = QLineEdit()
        self.api_region_input.setText(settings_manager.get("api_region", "global"))
        form_layout.addRow("API Region:", self.api_region_input)
        
        # Auto translate on paste
        self.auto_paste_check = ToggleSwitch()
        self.auto_paste_check.setChecked(settings_manager.get("auto_translate_paste", True))
        
        # We need to manually set the initial position for the animation state to reflect checked state
        if self.auto_paste_check.isChecked():
            self.auto_paste_check.position = 24
            
        form_layout.addRow("Auto-translate on paste:", self.auto_paste_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
    def save_settings(self):
        settings_manager.set("api_key", self.api_key_input.text().strip())
        settings_manager.set("api_region", self.api_region_input.text().strip())
        settings_manager.set("auto_translate_paste", self.auto_paste_check.isChecked())
        self.accept()
