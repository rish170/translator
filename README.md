# Universal Translator

A modern, professional-grade desktop Language Translation Tool built with Python 3.12+ and PyQt6. Powered by the **Microsoft Translator API (Azure Cognitive Services)** for enterprise-grade text translation and **Edge-TTS** for high-quality Neural Text-to-Speech.

---

## 🌟 Features

- **Real-Time Translation:** No "Translate" button required. Text is translated automatically as you type using a smart 300-500ms debounce timer to minimize API calls.
- **Fluent UI Design:** Beautiful, responsive interface inspired by Windows 11 Fluent Design, featuring seamless Dark and Light modes.
- **Premium Neural Voices:** High-quality native Text-to-Speech integration via `edge-tts` without any clunky browser dependencies.
- **Smart Caching:** Identical requests are instantly retrieved from a local SQLite cache rather than burning through your API quota.
- **History & Favorites Tracking:** Automatically logs translations. Easily search through your history, star your favorites, or export them.
- **Robust Exports:** Export your translation history cleanly to `.txt` or `.pdf` files.
- **Clipboard Integration:** "Auto-translate on paste" functionality and quick one-click copy buttons for both source and target text.

---

## 🛠️ Prerequisites

1. **Python 3.12 or higher** installed on your system.
2. A **Microsoft Azure Cognitive Services** account with an active Translator resource (Free tier gives you 2 million characters per month).

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd translator_app
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   - **Windows (Command Prompt / PowerShell):**
     ```powershell
     .\venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

1. Launch the application:
   ```bash
   python main.py
   ```
2. Click the **Settings (⚙️)** icon in the top right corner.
3. Enter your **Microsoft Translator API Key**.
4. Enter your **API Region** (e.g., `global`, `eastus`, `westeurope`).
5. Click **Save**. Your credentials are encrypted/masked and saved locally.

---

## ⌨️ Usage

- **Typing:** Simply select your source and target languages from the uneditable dropdowns (click the arrow to search within the popup) and start typing on the left. The right side updates automatically.
- **Text-to-Speech:** Click the speaker icon 🔊 below either text box to hear the text spoken aloud in its native accent.
- **Swap Languages:** Click the double-arrow icon ⮂ in the middle to instantly swap the source and target languages.
- **Theme Toggle:** Click the Moon/Sun icon 🌙 to switch between Dark and Light mode dynamically.
- **History:** Click the clock icon 🕒 to view your recent translations, search them, or export them as a PDF.

---

## 📁 Project Structure

```text
translator_app/
├── assets/
│   └── icons/               # SVG icons used in the application
├── services/
│   ├── cache.py             # SQLite caching logic to reduce API calls
│   ├── speech.py            # Edge-TTS generation and WinMM audio playback
│   └── translator.py        # Microsoft API integration and threading logic
├── storage/
│   ├── history.py           # Database models for History and Favorites
│   └── settings.py          # JSON-based local settings manager
├── styles/
│   ├── dark.qss             # Dark Mode stylesheet
│   └── light.qss            # Light Mode stylesheet
├── ui/
│   ├── components.py        # Custom UI widgets (ToggleSwitch, SearchableComboBox)
│   ├── history_panel.py     # PDF/TXT export and history UI
│   ├── main_window.py       # Core layout and debouncing logic
│   └── settings_dialog.py   # Settings window
├── main.py                  # Application entry point
└── requirements.txt         # Python package dependencies
```

---

## 📝 Dependencies

- `PyQt6` - For the modern graphical user interface.
- `requests` - For HTTP calls to the Microsoft Translator API.
- `edge-tts` - For neural Text-to-Speech.
- `fpdf2` - For exporting history to PDF.

---

## 🛡️ License

This project is licensed under the MIT License. See the `LICENSE` file for details.
