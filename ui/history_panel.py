import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QLineEdit, QPushButton, QLabel, QFileDialog
)
from storage.history import history_manager
from storage.settings import settings_manager
from ui.components import ToastNotification

class HistoryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("History & Favorites")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        header_layout.addWidget(title)
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_btn)
        layout.addLayout(header_layout)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history...")
        self.search_input.textChanged.connect(self.load_history)
        layout.addWidget(self.search_input)
        
        # Export
        export_layout = QHBoxLayout()
        export_txt_btn = QPushButton("Export TXT")
        export_txt_btn.clicked.connect(self.export_txt)
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)
        export_layout.addWidget(export_txt_btn)
        export_layout.addWidget(export_pdf_btn)
        layout.addLayout(export_layout)
        
        # List
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.load_history()
        
    def load_history(self):
        self.list_widget.clear()
        query = self.search_input.text().strip()
        items = history_manager.get_history(search_query=query if query else None)
        for row in items:
            text = f"{row[3].upper()} -> {row[4].upper()}\n{row[1]}\n---\n{row[2]}"
            item = QListWidgetItem(text)
            self.list_widget.addItem(item)
            
    def clear_history(self):
        history_manager.clear_history()
        self.load_history()
        
    def export_txt(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export History to TXT", "", "Text Files (*.txt)")
        if file_path:
            items = history_manager.get_history()
            with open(file_path, 'w', encoding='utf-8') as f:
                for row in items:
                    f.write(f"[{row[5]}] {row[3]} -> {row[4]}\n")
                    f.write(f"Source: {row[1]}\n")
                    f.write(f"Translated: {row[2]}\n")
                    f.write("-" * 40 + "\n")
            ToastNotification(self, "Exported to TXT").show_toast()
            
    def export_pdf(self):
        try:
            from fpdf import FPDF
        except ImportError:
            ToastNotification(self, "FPDF library not found.").show_toast()
            return
                
        file_path, _ = QFileDialog.getSaveFileName(self, "Export History to PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Using basic core font since Arial/Helvetica don't fully support unicode out of the box
            pdf.set_font("Helvetica", size=10)
            
            items = history_manager.get_history()
            for row in items:
                # Sanitize to latin-1 to prevent crash with standard fonts
                src_text = str(row[1]).encode('latin-1', 'replace').decode('latin-1')
                tgt_text = str(row[2]).encode('latin-1', 'replace').decode('latin-1')
                
                # Using write instead of multi_cell to avoid strict horizontal space calculation issues
                pdf.write(7, f"[{row[5]}] {row[3]} -> {row[4]}\n")
                pdf.write(5, f"Source: {src_text}\n")
                pdf.write(5, f"Translated: {tgt_text}\n")
                pdf.write(5, "-" * 60 + "\n")
            
            pdf.output(file_path)
            ToastNotification(self, "Exported to PDF!").show_toast()
        except Exception as e:
            print(f"PDF Export Error: {e}")
            ToastNotification(self, f"PDF Export Failed: {e}").show_toast()
