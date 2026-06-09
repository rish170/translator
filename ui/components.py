from PyQt6.QtWidgets import (
    QWidget, QLabel, QComboBox, QCompleter, 
    QGraphicsOpacityEffect, QVBoxLayout, QDialog, QLineEdit, QListWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QPoint, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QPainter, QMovie

class ToastNotification(QWidget):
    def __init__(self, parent=None, text="", duration=2000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(text)
        self.label.setObjectName("toastLabel")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_toast)
        self.duration = duration

    def show_toast(self):
        # Position toast at the bottom center of the parent
        if self.parent():
            parent_rect = self.parent().rect()
            toast_width = self.sizeHint().width()
            toast_height = self.sizeHint().height()
            x = parent_rect.x() + (parent_rect.width() - toast_width) // 2
            y = parent_rect.y() + parent_rect.height() - toast_height - 40
            self.move(x, y)

        self.show()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.timer.start(self.duration)

    def hide_toast(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()

class LoadingIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Translating...")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #0078D4; font-weight: bold;")
        self.hide()

    def start(self):
        self.show()

    def stop(self):
        self.hide()

class LanguagePopup(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.selected_item = None
        self.items = items
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search language...")
        self.search_box.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_box)
        
        self.list_widget = QListWidget()
        self.list_widget.addItems(self.items)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)
        
    def filter_items(self, text):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())
            
    def on_item_clicked(self, item):
        self.selected_item = item.text()
        self.accept()

import time

class SearchableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(False)
        self._all_items = []
        self._last_closed_time = 0
        
    def addItems(self, items):
        self._all_items.extend(items)
        super().addItems(items)
        
    def showPopup(self):
        # If the popup was closed less than 200ms ago, it means the user clicked 
        # the combobox specifically to close the popup. We shouldn't reopen it.
        if time.time() - self._last_closed_time < 0.2:
            return
            
        popup = LanguagePopup(self._all_items, self)
        pos = self.mapToGlobal(QPoint(0, self.height()))
        popup.setGeometry(pos.x(), pos.y(), self.width(), 300)
        
        if popup.exec() == QDialog.DialogCode.Accepted and popup.selected_item:
            self.setCurrentText(popup.selected_item)
            
        self._last_closed_time = time.time()

class ToggleSwitch(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._position = 3
        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setDuration(200)
        self.stateChanged.connect(self.setup_animation)
        
    @pyqtProperty(int)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    def setup_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(24)
        else:
            self.animation.setEndValue(3)
        self.animation.start()

    def hitButton(self, pos: QPoint) -> bool:
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        from storage.settings import settings_manager
        theme = settings_manager.get("theme", "light")
        bg_color = QColor("#555555") if theme == "dark" else QColor("#D4D4D4")
        if self.isChecked():
            bg_color = QColor("#107C10")

        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        rect = QRect(0, 0, self.width(), self.height())
        painter.drawRoundedRect(rect, 14, 14)

        handle_color = QColor("#FFFFFF")
        painter.setBrush(handle_color)
        painter.drawEllipse(self._position, 3, 22, 22)
        painter.end()

class LiveStatistics(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_label = QLabel("0 chars | 0 words")
        self.stats_label.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(self.stats_label)

    def update_stats(self, text):
        chars = len(text)
        words = len(text.split())
        self.stats_label.setText(f"{chars} chars | {words} words")
