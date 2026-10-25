"""Luma Reader: an offline Piper document reader and plain-text editor."""
from __future__ import annotations

import ctypes
import html
import json
import os
import shutil
import sys
import threading
from pathlib import Path

from PySide6.QtCore import (QAbstractNativeEventFilter, QEvent, QLockFile, QObject, QThread,
                           Qt, QTimer, Signal)
from PySide6.QtGui import QAction, QColor, QFont, QFontDatabase, QKeySequence, QPixmap, QTextCursor, QTextFormat
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QScrollArea, QSlider, QSpinBox, QSplitter, QTabWidget, QTextBrowser,
    QTextEdit, QVBoxLayout, QWidget)

from reader_core import (DATA, ROOT, VOICES, Cancelled, Document, Page, State, atomic_json,
    clean_pdf_text, discover_voices, load_document, ocr_pdf_page, pdf_key, python_position, qt_position, sentences)
from speech import Speech, export_audio
from rich_editor import NoteEditor
from studio import StudioFeatures, WrappingLayout
from appearance import place_edges

WELCOME = """Welcome to Luma Reader

Your documents. Your voices. Entirely on your computer.

Open a PDF, Word document, text file, or Markdown note to start listening. Your Piper voices are available in the voice selector below.

Press Play to listen from the beginning, or select a passage and choose Read selection. Click inside the text and choose Read from cursor to start there.

Scanned books are supported. Automatic offline OCR recognizes pages with very little selectable text. Use OCR this page to recover text and labels from a mixed page. OCR reads printed text; it does not explain the meaning of a diagram.

Create a new note to write and listen to your own words. PDF and Word files stay read-only; Make editable copy opens their text as a new draft.

To listen to text from another application, copy it, then press Control + Alt + R while Luma Reader is running. The shortcut reads the existing clipboard and never copies anything automatically.
"""


class Job(QThread):
    result = Signal(object)
    failure = Signal(str)
    progress = Signal(int, int, str)

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.cancel = threading.Event()

    def run(self):
        try:
            value = self.task(self.cancel.is_set, self.progress.emit)
            self.result.emit(value)
        except Cancelled:
            self.result.emit(None)
        except Exception as error:
            self.failure.emit(str(error))


class Hotkey(QAbstractNativeEventFilter):
    ID = 0x4C52

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.registered = False
        if sys.platform == "win32":
            # MOD_CONTROL | MOD_ALT | MOD_NOREPEAT; R. Register only for this running app.
            self.registered = bool(ctypes.windll.user32.RegisterHotKey(None, self.ID, 0x4003, ord("R")))

    def nativeEventFilter(self, event_type, message):
        if sys.platform == "win32":
            from ctypes.wintypes import MSG
            msg = MSG.from_address(int(message))
            if msg.message == 0x0312 and msg.wParam == self.ID:
                QTimer.singleShot(0, self.callback)
                return True, 0
        return False, 0

    def release(self):
        if self.registered:
            ctypes.windll.user32.UnregisterHotKey(None, self.ID)
            self.registered = False


class Reader(StudioFeatures, QMainWindow):
    def __init__(self, register_hotkey=True):
        super().__init__()
        # Qt's offscreen backend does not enumerate Windows fonts. Load the local
        # system faces explicitly if needed; fonts are never copied or bundled.
        if "Segoe UI" not in QFontDatabase.families() and sys.platform == "win32":
            for font_name in ("segoeui.ttf", "seguisb.ttf", "segoeuib.ttf", "seguiemj.ttf"):
                QFontDatabase.addApplicationFont(str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / font_name))
        self.state = State()
        self.document = Document(None, [Page(WELCOME)], "Welcome")
        self.parts = []
        self.current = 0
        self.job = None
        self.close_pending = False
        self.pdf = None
        self.editable = False
        self._updating = False
        self.voices = []
        self.setWindowTitle("Luma Reader")
        self.resize(1340, 880)
        self.setMinimumSize(1040, 680)
        self.speech = Speech(self)
        self.speech.sentence_started.connect(self.highlight)
        self.speech.status.connect(self.set_status)
        self.speech.failed.connect(self.speech_error)
        self.speech.finished.connect(self.reading_finished)
        self._build_ui()
        self._build_menu()
        self.upgrade_ui()
        self.refresh_voices()
        self.dark.setChecked(self.state.value.get("dark", False))
        self.apply_theme()
        self.apply_document(self.document, restore=False)
        self.hotkey = Hotkey(self.read_clipboard) if register_hotkey else None
        if self.hotkey:
            QApplication.instance().installNativeEventFilter(self.hotkey)
        self.clip_button.setToolTip("Copy text in any app, then press Ctrl+Alt+R" if self.hotkey and self.hotkey.registered
                                    else "Global shortcut unavailable. Use this button to read copied text.")
        self.refresh_recent()
        available = self.screen().availableGeometry()
        if available.width() < 1200:
            self.splitter.widget(0).hide()
        self.resize(min(1340, available.width()), min(880, available.height()))
        self.move(available.topLeft())
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(4000)
        self.save_timer.timeout.connect(self.save_progress)
        self.save_timer.start()

    def button(self, text, callback, primary=False):
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        return button

    def _build_ui(self):
        shell = QWidget()
        self.setCentralWidget(shell)
        outer = QVBoxLayout(shell)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        bar = QHBoxLayout(header)
        bar.setContentsMargins(24, 16, 24, 16)
        brand = QLabel("◒  LUMA")
        brand.setObjectName("brand")
        bar.addWidget(brand)
        subtitle = QLabel("READER & NOTES")
        subtitle.setObjectName("muted")
        bar.addWidget(subtitle)
        bar.addStretch()
        badge = QLabel("●  Offline · Piper + OCR")
        badge.setObjectName("badge")
        bar.addWidget(badge)
        self.dark = QCheckBox("Dark theme")
        self.dark.toggled.connect(self.apply_theme)
        bar.addWidget(self.dark)
        outer.addWidget(header)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(self.splitter, 1)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(220)
        sidebar.setMaximumWidth(290)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_content = QWidget()
        side = QVBoxLayout(sidebar_content)
        self.sidebar_scroll.setWidget(sidebar_content)
        sidebar_layout.addWidget(self.sidebar_scroll)
        side.setContentsMargins(18, 22, 18, 16)
        side.setSpacing(12)
        side.addWidget(self.button("+  Open document", self.open_dialog, True))
        side.addWidget(self.button("New note", self.new_note))
        self.clip_button = self.button("Read copied text", self.read_clipboard)
        side.addWidget(self.clip_button)
        self.side_tabs = QTabWidget()
        # Keep document lists usable; the containing sidebar scrolls when its
        # actions and help text need more height than the current window offers.
        self.side_tabs.setMinimumHeight(180)
        self.recent = QListWidget()
        self.recent.itemActivated.connect(lambda item: self.open_path(Path(item.data(Qt.ItemDataRole.UserRole))))
        self.outline = QListWidget()
        self.outline.itemActivated.connect(self.navigate_item)
        self.bookmarks = QListWidget()
        self.bookmarks.itemActivated.connect(self.goto_bookmark)
        self.side_tabs.addTab(self.recent, "Recent")
        self.side_tabs.addTab(self.outline, "Outline")
        self.side_tabs.addTab(self.bookmarks, "Saved")
        side.addWidget(self.side_tabs, 1)
        side.addWidget(self.button("Bookmark position", self.add_bookmark))
        side.addWidget(self.button("Remove bookmark", self.remove_bookmark))
        tip = QLabel("Copy text in another app\nCtrl + Alt + R to listen\n\nPDF / DOCX / TXT / MD")
        tip.setObjectName("muted")
        tip.setWordWrap(True)
        side.addWidget(tip)
        self.splitter.addWidget(sidebar)

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(28, 22, 28, 18)
        main_layout.setSpacing(12)
        self.title = QLabel("Welcome")
        self.title.setObjectName("documentTitle")
        self.title.setWordWrap(True)
        main_layout.addWidget(self.title)
        self.meta = QLabel()
        self.meta.setObjectName("muted")
        main_layout.addWidget(self.meta)
        tools = WrappingLayout()
        self.reading_tools = tools
        tools.addWidget(self.button("Read selection", self.read_selection))
        tools.addWidget(self.button("Read from cursor", self.read_cursor))
        self.draft_button = self.button("Make editable copy", self.make_draft)
        tools.addWidget(self.draft_button)
        tools.addStretch()
        tools.addWidget(QLabel("Text size"))
        self.font_size = QSpinBox()
        self.font_size.setRange(12, 30)
        self.font_size.setValue(self.state.value.get("font_size", 17))
        self.font_size.valueChanged.connect(self.change_font)
        tools.addWidget(self.font_size)
        main_layout.addLayout(tools)
        self.content = QSplitter(Qt.Orientation.Horizontal)
        self.tabs = QTabWidget()
        self.editor = NoteEditor()
        self.editor.setObjectName("readingText")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.editor.textChanged.connect(self.text_changed)
        self.editor.document().modificationChanged.connect(self.update_title)
        self.tabs.addTab(self.editor, "Reading text")
        self.markdown = QTextBrowser()
        self.markdown.setOpenExternalLinks(False)
        self.markdown.anchorClicked.connect(lambda _: self.set_status("External links are disabled in the reading preview."))
        self.tabs.addTab(self.markdown, "Markdown preview")
        self.tabs.currentChanged.connect(self.update_markdown)
        self.content.addWidget(self.tabs)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_label = QLabel("Original page")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.preview_scroll.setWidget(self.preview_label)
        self.preview_scroll.setMinimumWidth(250)
        self.content.addWidget(self.preview_scroll)
        self.content.setSizes([650, 400])
        self.content.splitterMoved.connect(lambda *_: self.render_page())
        main_layout.addWidget(self.content, 1)

        self.pdf_controls = QWidget()
        pdf_row = QHBoxLayout(self.pdf_controls)
        pdf_row.setContentsMargins(0, 0, 0, 0)
        pdf_row.addWidget(QLabel("Page"))
        self.page_number = QSpinBox()
        self.page_number.setRange(1, 1)
        self.page_number.valueChanged.connect(self.goto_page)
        pdf_row.addWidget(self.page_number)
        self.page_count = QLabel("/ 1")
        pdf_row.addWidget(self.page_count)
        self.show_original = QCheckBox("Original page")
        self.show_original.setChecked(True)
        self.show_original.toggled.connect(self.toggle_preview)
        pdf_row.addWidget(self.show_original)
        pdf_row.addStretch()
        self.ocr_mode = QComboBox()
        self.ocr_mode.addItem("Automatic OCR", "auto")
        self.ocr_mode.addItem("OCR every page", "force")
        self.ocr_mode.addItem("Selectable text only", "off")
        self.ocr_mode.setToolTip("Applies when opening the next PDF. Automatic OCR handles scanned pages; force OCR recovers image labels on mixed pages.")
        pdf_row.addWidget(self.ocr_mode)
        self.ocr_button = self.button("OCR this page", self.ocr_current)
        pdf_row.addWidget(self.ocr_button)
        main_layout.addWidget(self.pdf_controls)

        self.find_row = QWidget()
        search = QHBoxLayout(self.find_row)
        search.setContentsMargins(0, 0, 0, 0)
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find in document…")
        self.find_input.returnPressed.connect(self.find_next)
        search.addWidget(self.find_input, 1)
        search.addWidget(self.button("Next", self.find_next))
        search.addWidget(self.button("Replace…", self.replace_dialog))
        search.addWidget(self.button("Close", lambda: self.find_row.hide()))
        self.find_row.hide()
        main_layout.addWidget(self.find_row)
        self.job_panel = QWidget()
        job_layout = QHBoxLayout(self.job_panel)
        job_layout.setContentsMargins(0, 0, 0, 0)
        self.job_progress = QProgressBar()
        job_layout.addWidget(self.job_progress, 1)
        job_layout.addWidget(self.button("Cancel", self.cancel_job))
        self.job_panel.hide()
        main_layout.addWidget(self.job_panel)
        self.splitter.addWidget(main)
        self.splitter.setSizes([245, 1095])

        bottom = QFrame()
        bottom.setObjectName("playback")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 14, 24, 14)
        controls = WrappingLayout()
        controls.setSpacing(10)
        controls.addWidget(self.button("Previous", lambda: self.skip(-1)))
        self.play_button = self.button("▶  Play", self.play_pause, True)
        self.play_button.setMinimumWidth(110)
        controls.addWidget(self.play_button)
        controls.addWidget(self.button("Stop", self.stop))
        controls.addWidget(self.button("Next", lambda: self.skip(1)))
        controls.addWidget(QLabel("Voice"))
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumWidth(150)
        self.voice_combo.currentIndexChanged.connect(self.voice_changed)
        controls.addWidget(self.voice_combo, 1)
        self.speaker_combo = QComboBox()
        self.speaker_combo.setMaximumWidth(130)
        self.speaker_combo.currentIndexChanged.connect(self.voice_option_changed)
        controls.addWidget(self.speaker_combo)
        controls.addWidget(self.button("Test", self.test_voice))
        controls.addWidget(QLabel("Speed"))
        self.speed = QDoubleSpinBox()
        self.speed.setRange(0.5, 2.5)
        self.speed.setSingleStep(0.1)
        self.speed.setSuffix("×")
        self.speed.setValue(self.state.value.get("speed", 1.0))
        self.speed.valueChanged.connect(self.voice_option_changed)
        controls.addWidget(self.speed)
        controls.addWidget(QLabel("Volume"))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(self.state.value.get("volume", 80))
        self.volume.setMaximumWidth(85)
        self.volume.valueChanged.connect(lambda value: self.speech.output.setVolume(value / 100))
        self.speech.output.setVolume(self.volume.value() / 100)
        controls.addWidget(self.volume)
        bottom_layout.addLayout(controls)
        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("muted")
        status_row.addWidget(self.status_label, 1)
        self.read_progress = QLabel("")
        self.read_progress.setObjectName("muted")
        status_row.addWidget(self.read_progress)
        bottom_layout.addLayout(status_row)
        outer.addWidget(bottom)
        self.change_font()
        self.setAcceptDrops(True)

    def action(self, menu, name, callback, shortcut=None):
        action = QAction(name, self)
        action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        menu.addAction(action)
        return action

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        self.action(file_menu, "Open document…", self.open_dialog, "Ctrl+O")
        self.action(file_menu, "New note", self.new_note, "Ctrl+N")
        self.action(file_menu, "Save", self.save, "Ctrl+S")
        self.action(file_menu, "Save as…", lambda: self.save(True), "Ctrl+Shift+S")
        self.action(file_menu, "Export audio…", self.export_dialog, "Ctrl+E")
        self.action(file_menu, "Make editable copy", self.make_draft)
        file_menu.addSeparator()
        self.action(file_menu, "Exit", self.close, "Alt+F4")
        edit = self.menuBar().addMenu("Edit")
        self.action(edit, "Undo", self.editor.undo, "Ctrl+Z")
        self.action(edit, "Redo", self.editor.redo, "Ctrl+Y")
        self.action(edit, "Find", self.show_find, "Ctrl+F")
        self.action(edit, "Replace…", self.replace_dialog, "Ctrl+H")
        self.action(edit, "Read copied text", self.read_clipboard)
        audio = self.menuBar().addMenu("Read")
        self.action(audio, "Play / pause", self.play_pause, "F5")
        self.action(audio, "Stop", self.stop, "F6")
        self.action(audio, "Read selection", self.read_selection, "Ctrl+Shift+R")
        self.action(audio, "Read from cursor", self.read_cursor, "Ctrl+R")
        self.action(audio, "Previous sentence", lambda: self.skip(-1), "Alt+Left")
        self.action(audio, "Next sentence", lambda: self.skip(1), "Alt+Right")
        audio.addSeparator()
        self.action(audio, "OCR current PDF page", self.ocr_current)
        self.action(audio, "Restore original PDF page text", self.restore_page_text)
        voices = self.menuBar().addMenu("Voices")
        self.action(voices, "Import Piper voice…", self.import_voice)
        self.action(voices, "Refresh voices", self.refresh_voices)
        self.action(voices, "Test selected voice", self.test_voice)
        help_menu = self.menuBar().addMenu("Help")
        self.action(help_menu, "User guide", self.show_guide)
        self.action(help_menu, "About and licenses", self.about)

    def _base_apply_theme(self, *_):
        if not hasattr(self, "dark"):
            return
        dark = self.dark.isChecked()
        bg, panel, text, muted, border, accent, tint = (
            ("#171e25", "#202a33", "#edf3f3", "#a3b5bf", "#35434e", "#8cdbc4", "#293f3a") if dark else
            ("#f4f6f5", "#ffffff", "#203b39", "#697d7b", "#dce5e2", "#176f60", "#e5f2ed"))
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background: {bg}; color: {text}; font-family: 'Segoe UI'; font-size: 13px; }}
            QMenuBar, QMenu, QDialog {{ background: {panel}; }}
            QMenu::item:selected {{ background: {tint}; }}
            #header, #playback {{ background: {panel}; border-bottom: 1px solid {border}; }}
            #header QLabel, #playback QLabel, #header QCheckBox {{ background: transparent; }}
            #sidebar {{ background: {panel}; border-right: 1px solid {border}; }}
            #brand {{ font-size: 24px; font-weight: 750; letter-spacing: 3px; color: {accent}; }}
            #documentTitle {{ font-size: 25px; font-weight: 650; }}
            #muted {{ color: {muted}; font-size: 12px; }}
            #badge {{ color: {accent}; border-radius: 12px; padding: 5px 12px; background: {tint}; }}
            QPushButton {{ background: {panel}; border: 1px solid {border}; border-radius: 7px; padding: 8px 13px; }}
            QPushButton:hover {{ background: {tint}; border-color: {accent}; }}
            QPushButton:disabled {{ color: {muted}; }}
            QPushButton#primary {{ background: {'#286c5e' if dark else accent}; color: white; border-color: transparent; font-weight: 600; }}
            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{ background: {panel}; border: 1px solid {border}; border-radius: 6px; padding: 6px; min-height: 22px; }}
            QPlainTextEdit, QTextBrowser {{ background: {panel}; color: {text}; border: 1px solid {border}; border-radius: 10px; padding: 24px; selection-background-color: #84c9b5; selection-color: #142e28; }}
            QListWidget {{ background: {panel}; border: none; outline: none; }}
            QListWidget::item {{ padding: 9px 6px; border-radius: 5px; }}
            QListWidget::item:selected {{ background: {tint}; color: {text}; }}
            QTabWidget::pane {{ border: none; }}
            QTabBar::tab {{ padding: 8px 11px; background: transparent; color: {muted}; }}
            QTabBar::tab:selected {{ color: {accent}; border-bottom: 2px solid {accent}; }}
            QScrollArea {{ border: 1px solid {border}; border-radius: 8px; }}
            QProgressBar {{ border: 1px solid {border}; border-radius: 5px; text-align: center; min-height: 22px; }}
            QProgressBar::chunk {{ background: {'#286c5e' if dark else '#a4d5c6'}; }}
            QSplitter::handle {{ background: {border}; width: 2px; }}
            QToolTip {{ background: {panel}; color: {text}; border: 1px solid {border}; padding: 6px; }}
        """)

    def change_font(self, *_):
        if hasattr(self, "font_size"):
            font = QFont("Segoe UI", self.font_size.value())
            self.editor.setFont(font)
            self.markdown.setFont(font)
            self.editor.setStyleSheet(f"font-size: {self.font_size.value()}pt;")
            self.markdown.setStyleSheet(f"font-size: {self.font_size.value()}pt;")

    def refresh_voices(self):
        previous = self.voice_combo.currentData() or self.state.value.get("voice")
        self.voices, issues = discover_voices()
        self.voice_combo.blockSignals(True)
        self.voice_combo.clear()
        for voice in self.voices:
            self.voice_combo.addItem(voice.name.title(), str(voice.path))
        index = self.voice_combo.findData(previous)
        if index >= 0:
            self.voice_combo.setCurrentIndex(index)
        self.voice_combo.blockSignals(False)
        self.voice_changed()
        if issues:
            self.set_status(f"{len(self.voices)} voices ready; {len(issues)} incomplete. See Voices → Import.")

    def voice_changed(self, *_):
        self.stop()
        self.speaker_combo.blockSignals(True)
        self.speaker_combo.clear()
        voice = self.selected_voice()
        if voice:
            for name, number in voice.speakers.items():
                self.speaker_combo.addItem(name, number)
        self.speaker_combo.setVisible(self.speaker_combo.count() > 1)
        self.speaker_combo.blockSignals(False)

    def selected_voice(self):
        index = self.voice_combo.currentIndex()
        return self.voices[index] if 0 <= index < len(self.voices) else None

    def voice_option_changed(self, *_):
        was_active = self.speech.active
        index = self.current
        self.stop()
        if was_active and self.parts:
            self.start_speech(index)

    def import_voice(self):
        if self.job:
            return
        name, _ = QFileDialog.getOpenFileName(self, "Choose a Piper voice model", str(VOICES), "Piper voice (*.onnx)")
        if not name:
            return
        source = Path(name)
        config_path = Path(name + ".json")
        if not config_path.exists():
            selected, _ = QFileDialog.getOpenFileName(self, "Locate the matching .onnx.json configuration", str(source.parent), "Voice configuration (*.json)")
            if not selected:
                return
            config_path = Path(selected)
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            if not config.get("phoneme_id_map") or not config.get("audio", {}).get("sample_rate"):
                raise ValueError("This is not a complete Piper voice configuration.")
            target = VOICES / source.name
            VOICES.mkdir(parents=True,exist_ok=True)
            target_config = Path(str(target) + ".json")
            if source.resolve() != target.resolve():
                if target.exists() or target_config.exists():
                    QMessageBox.information(self, "Voice already exists", "A voice with this filename is already in the voice folder. Rename the new pair before importing it.")
                    return
                shutil.copy2(source, target)
                try:
                    shutil.copy2(config_path, target_config)
                except Exception:
                    target.unlink(missing_ok=True)
                    raise
            elif config_path.resolve() != target_config.resolve():
                shutil.copy2(config_path, target_config)
            self.refresh_voices()
            self.voice_combo.setCurrentIndex(self.voice_combo.findData(str(target)))
            self.set_status("Voice imported. Click Test to check it.")
        except Exception as error:
            self.error(str(error))

    def set_status(self, text):
        self.status_label.setText(text)

    def error(self, text):
        self.set_status(text)
        QMessageBox.warning(self, "Luma Reader", text)

    def speech_error(self, text):
        self.play_button.setText("▶  Play")
        self.editor.setExtraSelections([])
        self.error(text)

    def _base_stop(self):
        self.speech.stop()
        if getattr(self, "testing_voice", False):
            self.testing_voice = False
            self.parts = []
            self.current = 0
        if hasattr(self, "play_button"):
            self.play_button.setText("▶  Play")
            self.editor.setExtraSelections([])
            self.set_status("Stopped")

    def _base_start_speech(self, index=0):
        if self.job:
            self.set_status("Finish or cancel the current document task first.")
            return
        voice = self.selected_voice()
        if not voice:
            self.error("Import a Piper .onnx voice and its matching .onnx.json file from the Voices menu.")
            return
        if not self.parts:
            self.set_status("There is no readable text. For a scanned PDF, try OCR this page.")
            return
        index = max(0, min(index, len(self.parts) - 1))
        self.current = index
        self.speech.start(self.parts, voice, index, self.speed.value(), self.speaker_combo.currentData() or 0)
        self.play_button.setText("Pause")

    def play_pause(self):
        if self.speech.active:
            self.speech.toggle_pause()
            self.play_button.setText("▶  Resume" if self.speech.paused else "Pause")
        else:
            if not self.parts:
                self.parts = sentences(self.editor.toPlainText())
                offset = python_position(self.editor.toPlainText(), self.editor.textCursor().position())
                self.current = next((i for i, part in enumerate(self.parts) if part.end > offset), 0)
            self.start_speech(self.current)

    def read_selection(self):
        text = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            self.set_status("Select some reading text first.")
            return
        self.parts = sentences(text, python_position(text, cursor.selectionStart()), python_position(text, cursor.selectionEnd()))
        self.start_speech()

    def read_cursor(self):
        text = self.editor.toPlainText()
        self.parts = sentences(text, python_position(text, self.editor.textCursor().position()))
        self.start_speech()

    def skip(self, direction):
        if not self.parts:
            self.parts = sentences(self.editor.toPlainText())
        self.start_speech(self.current + direction)

    def test_voice(self):
        self.stop()
        self.parts = sentences("Hello. This is your selected Piper voice, speaking entirely on your computer.")
        self.testing_voice = True
        self.start_speech()

    def _base_highlight(self, index):
        self.current = index
        self.read_progress.setText(f"Sentence {index + 1} / {len(self.parts)}")
        if getattr(self, "testing_voice", False):
            return
        part = self.parts[index]
        text = self.editor.toPlainText()
        cursor = QTextCursor(self.editor.document())
        cursor.setPosition(qt_position(text, part.start))
        cursor.setPosition(qt_position(text, part.end), QTextCursor.MoveMode.KeepAnchor)
        highlight = QTextEdit.ExtraSelection()
        highlight.cursor = cursor
        highlight.format.setBackground(QColor("#cbe8a9"))
        highlight.format.setForeground(QColor("#20351e"))
        self.editor.setExtraSelections([highlight])
        scroll_cursor = QTextCursor(cursor)
        scroll_cursor.setPosition(qt_position(text, part.start))
        self.editor.setTextCursor(scroll_cursor)
        self.editor.ensureCursorVisible()
        if self.pdf:
            page = self.page_for_offset(part.start)
            if self.page_number.value() != page + 1:
                self.page_number.blockSignals(True)
                self.page_number.setValue(page + 1)
                self.page_number.blockSignals(False)
                self.render_page()

    def _base_reading_finished(self):
        self.play_button.setText("▶  Play")
        self.editor.setExtraSelections([])
        self.testing_voice = False
        self.current = 0
        self.parts = []

    def _base_confirm_unsaved(self):
        if not self.editor.document().isModified():
            return True
        choice = QMessageBox.question(self, "Save your note?", "This note has unsaved changes.",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if choice == QMessageBox.StandardButton.Save:
            return self.save()
        return choice == QMessageBox.StandardButton.Discard

    def open_dialog(self):
        if self.job:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open a document", str(ROOT.parent),
            "Documents (*.pdf *.docx *.txt *.md *.markdown *.html *.htm);;All files (*)")
        if path:
            self.open_path(Path(path))

    def open_path(self, path):
        if self.job or not self.confirm_unsaved():
            return
        self.save_progress()
        self.stop()
        self.testing_voice = False
        mode = self.ocr_mode.currentData()
        self.run_job(lambda cancel, progress: load_document(path, mode, progress, cancel), self.document_loaded)

    def document_loaded(self, document):
        if document is not None:
            self.apply_document(document)
            self.set_status("Ready · OCR text may need correction, especially columns and equations." if any("OCR" in p.method for p in document.pages) else "Ready")

    def _base_apply_document(self, document, restore=True):
        self.stop()
        self.parts = []
        self.current = 0
        self.testing_voice = False
        if self.pdf:
            self.pdf.close()
            self.pdf = None
        self.document = document
        self.editable = document.path is None and document.title != "Welcome" or bool(document.path and document.path.suffix.lower() in {".txt", ".md", ".markdown"})
        self._updating = True
        self.editor.setPlainText(document.text)
        self.editor.setReadOnly(not self.editable)
        self.editor.setUndoRedoEnabled(self.editable)
        self.editor.document().setModified(False)
        self._updating = False
        self.tabs.setTabText(0, "Editor" if self.editable else "Reading text")
        is_md = bool(document.path and document.path.suffix.lower() in {".md", ".markdown"})
        self.tabs.setTabVisible(1, is_md)
        self.tabs.setCurrentIndex(0)
        if document.path and document.path.suffix.lower() == ".pdf":
            import pymupdf as fitz
            self.pdf = fitz.open(document.path)
        self.pdf_controls.show()
        self.page_number.setEnabled(bool(self.pdf))
        self.show_original.setEnabled(bool(self.pdf))
        self.ocr_button.setEnabled(bool(self.pdf))
        self.page_number.blockSignals(True)
        self.page_number.setRange(1, max(1, len(document.pages)))
        self.page_number.setValue(1)
        self.page_number.blockSignals(False)
        self.page_count.setText(f"/ {len(document.pages)}")
        self.preview_scroll.setVisible(bool(self.pdf) and self.show_original.isChecked())
        self.draft_button.setVisible(not self.editable)
        self.build_outline()
        self.refresh_bookmarks()
        if document.path:
            key = str(document.path.resolve())
            position = self.state.value.get("positions", {}).get(key, 0) if restore else 0
            self.set_cursor(min(position, len(document.text)))
            self.state.remember(document.path, position)
            self.refresh_recent()
        self.update_title()
        self.render_page()
        QTimer.singleShot(0, self.render_page)
        self.update_markdown()

    def _base_update_title(self, *_):
        dirty = self.editor.document().isModified()
        self.title.setText(self.document.title + (" •" if dirty else ""))
        self.setWindowTitle(f"{'* ' if dirty else ''}{self.document.title} — Luma Reader")
        words = len(self.editor.toPlainText().split())
        kind = "Editable note" if self.editable else "Read-only source · Make an editable copy to change text"
        self.meta.setText(f"{words:,} words  ·  {kind}")

    def text_changed(self):
        if self._updating:
            return
        self.stop()
        self.testing_voice = False
        self.parts = []
        self.current = 0
        self.update_title()

    def new_note(self):
        if self.job or not self.confirm_unsaved():
            return
        self.save_progress()
        self.apply_document(Document(None, [Page("")], "Untitled note"))
        self.editor.setFocus()
        self.set_status("New note · Save as TXT or Markdown")

    def _base_make_draft(self):
        if self.job or not self.confirm_unsaved():
            return
        text = self.editor.toPlainText()
        self.save_progress()
        self.apply_document(Document(None, [Page(text)], "Editable copy"))
        self.editor.document().setModified(True)
        self.set_status("Editable copy · Save as TXT or Markdown. The original document is preserved.")

    def _base_save(self, save_as=False):
        if self.job:
            return False
        path = self.document.path
        if not self.editable:
            save_as = True
        if save_as or path is None:
            name, _ = QFileDialog.getSaveFileName(self, "Save reading text", str(ROOT / "note.txt"),
                "Text file (*.txt);;Markdown (*.md)")
            if not name:
                return False
            path = Path(name)
            if not path.suffix:
                path = path.with_suffix(".txt")
            if path.suffix.lower() not in {".txt", ".md", ".markdown"}:
                self.error("Save this text as .txt or .md. PDF and DOCX layout editing is not supported.")
                return False
        try:
            import tempfile
            fd, temp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                    stream.write(self.editor.toPlainText())
                os.replace(temp, path)
            finally:
                Path(temp).unlink(missing_ok=True)
            if not self.editable or self.document.path != path:
                self.apply_document(Document(path, [Page(self.editor.toPlainText())], path.name), restore=False)
            self.editor.document().setModified(False)
            self.set_status(f"Saved {path.name}")
            return True
        except OSError as error:
            self.error(f"Could not save: {error}")
            return False

    def _base_save_progress(self):
        if self.close_pending:
            return
        try:
            text = self.editor.toPlainText()
            self.state.value.update(dark=self.dark.isChecked(), font_size=self.font_size.value(),
                speed=self.speed.value(), volume=self.volume.value(), voice=self.voice_combo.currentData())
            if self.document.path:
                self.state.remember(self.document.path, python_position(text, self.editor.textCursor().position()))
            else:
                self.state.save()
        except OSError:
            self.set_status("Reading is available, but settings could not be saved in the project folder.")

    def refresh_recent(self):
        self.recent.clear()
        for path in self.state.value.get("recent", []):
            item = QListWidgetItem(Path(path).name)
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent.addItem(item)

    def build_outline(self):
        self.outline.clear()
        for title, page in self.document.headings:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, ("heading", title, page))
            self.outline.addItem(item)
        if self.pdf:
            for i, page in enumerate(self.document.pages):
                item = QListWidgetItem(f"Page {i + 1} · {page.method}")
                item.setData(Qt.ItemDataRole.UserRole, ("page", "", i))
                self.outline.addItem(item)
        elif self.document.path and self.document.path.suffix.lower() in {".md", ".markdown"}:
            import re
            for match in re.finditer(r"(?m)^#{1,6}\s+(.+)$", self.editor.toPlainText()):
                item = QListWidgetItem(match.group(1))
                item.setData(Qt.ItemDataRole.UserRole, ("offset", "", match.start()))
                self.outline.addItem(item)

    def navigate_item(self, item):
        kind, title, value = item.data(Qt.ItemDataRole.UserRole)
        self.stop()
        self.parts = []
        self.current = 0
        if kind == "offset":
            self.set_cursor(value)
        elif self.pdf:
            self.goto_page(value + 1)
        else:
            offset = self.editor.toPlainText().find(title)
            if offset >= 0:
                self.set_cursor(offset)

    def set_cursor(self, offset):
        text = self.editor.toPlainText()
        cursor = self.editor.textCursor()
        cursor.setPosition(qt_position(text, max(0, min(offset, len(text)))))
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        if self.pdf:
            self.page_number.blockSignals(True)
            self.page_number.setValue(self.page_for_offset(offset) + 1)
            self.page_number.blockSignals(False)

    def page_for_offset(self, offset):
        page, start = 0, 0
        for i, source_page in enumerate(self.document.pages):
            if start > offset:
                break
            page = i
            start += len(source_page.text) + 2
        return page

    def _base_goto_page(self, number):
        if not self.pdf:
            return
        self.stop()
        self.parts = []
        self.current = 0
        self.page_number.blockSignals(True)
        self.page_number.setValue(number)
        self.page_number.blockSignals(False)
        self.set_cursor(self.document.page_start(number - 1))
        self.render_page()

    def _base_render_page(self):
        if not self.pdf or not self.preview_scroll.isVisible():
            return
        try:
            page = self.pdf[self.page_number.value() - 1]
            width = max(250, self.preview_scroll.viewport().width() - 20)
            pix = page.get_pixmap(matrix=__import__("pymupdf").Matrix(width / page.rect.width, width / page.rect.width), alpha=False)
            image = QPixmap()
            image.loadFromData(pix.tobytes("png"))
            self.preview_label.setPixmap(image)
            self.preview_label.setToolTip(f"Page {self.page_number.value()} · {self.document.pages[self.page_number.value()-1].method}")
        except Exception as error:
            self.set_status(f"Page preview unavailable: {error}")

    def toggle_preview(self, visible):
        self.preview_scroll.setVisible(bool(self.pdf) and visible)
        QTimer.singleShot(0, self.render_page)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        place_edges(self)
        if hasattr(self, "format_bar"):
            self.update_compact_workspace()
        if hasattr(self, "preview_scroll"):
            QTimer.singleShot(100, self.render_page)

    def ocr_current(self):
        if not self.pdf or self.job:
            return
        index = self.page_number.value() - 1
        path = self.document.path
        def task(cancel, progress):
            progress(0, 1, f"Recognizing page {index + 1} · offline OCR")
            result = ocr_pdf_page(path, index)
            return None if cancel() else result
        def done(page):
            if page is None:
                return
            self.document.pages[index] = page
            self.apply_document(self.document, restore=False)
            self.goto_page(index + 1)
            self.set_status("OCR complete · Text, captions, and labels recovered where legible. Make an editable copy to correct them.")
        self.run_job(task, done)

    def restore_page_text(self):
        if not self.pdf or self.job:
            return
        index = self.page_number.value() - 1
        page = Page(clean_pdf_text(self.pdf[index].get_text(sort=True)), "Text")
        try:
            (DATA / "ocr" / pdf_key(self.document.path) / f"{index}.json").unlink(missing_ok=True)
        except OSError as error:
            self.error(f"Could not remove this page's OCR cache: {error}")
            return
        self.document.pages[index] = page
        self.apply_document(self.document, restore=False)
        self.goto_page(index + 1)
        self.set_status("Restored the PDF's original selectable text for this page.")

    def run_job(self, task, result):
        if self.job:
            return
        self.stop()
        self.job = Job(task, self)
        self.job.result.connect(result)
        self.job.failure.connect(self.error)
        self.job.progress.connect(self.show_progress)
        self.job.finished.connect(self.job_done)
        self.format_bar.setEnabled(False)
        self.job_panel.show()
        self.job_progress.setRange(0, 0)
        self.editor.setReadOnly(True)
        self.job.start()

    def show_progress(self, value, total, text):
        self.job_progress.setRange(0, max(1, total))
        self.job_progress.setValue(value)
        self.job_progress.setFormat(f"{value} / {total}")
        self.set_status(text)

    def cancel_job(self):
        if self.job:
            self.job.cancel.set()
            self.set_status("Cancelling after the current page or speech chunk…")

    def job_done(self):
        cancelled = self.job.cancel.is_set()
        self.job.deleteLater()
        self.job = None
        self.job_panel.hide()
        self.format_bar.setEnabled(self.editable and self.note_format != "plain")
        self.editor.setReadOnly(not self.editable)
        if cancelled:
            self.set_status("Task cancelled. Completed OCR pages remain cached.")
        if self.close_pending:
            QTimer.singleShot(0, self.close)

    def export_dialog(self):
        if self.job:
            return
        voice = self.selected_voice()
        if not voice:
            self.error("Import a voice first.")
            return
        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        parts = sentences(text, python_position(text, cursor.selectionStart()), python_position(text, cursor.selectionEnd())) if cursor.hasSelection() else sentences(text)
        if not parts:
            self.set_status("There is no text to export.")
            return
        from runtime_paths import EXPORT_ROOT
        name, _ = QFileDialog.getSaveFileName(self, "Export selection as WAV" if cursor.hasSelection() else "Export document as WAV", str(EXPORT_ROOT / "reading.wav"), "WAV audio (*.wav)")
        if not name:
            return
        target = Path(name)
        if target.suffix.lower() != ".wav":
            target = target.with_suffix(".wav")
        parts = self.prepare_speech(parts)
        if not parts:
            self.set_status("No spoken content remains after applying the reading rules.")
            return
        speed, speaker = self.speed.value(), self.speaker_combo.currentData() or 0
        self.run_job(lambda cancel, progress: export_audio(parts, voice, target, speed, speaker, progress, cancel),
                     lambda saved: self.set_status(f"Audio saved: {target.name}" if saved else "Audio export cancelled"))

    def show_find(self):
        self.find_row.show()
        self.find_input.setFocus()

    def find_next(self):
        query = self.find_input.text()
        if query:
            if not self.editor.find(query):
                cursor = self.editor.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.Start)
                self.editor.setTextCursor(cursor)
                if not self.editor.find(query):
                    self.set_status("No matching text found.")

    def replace_dialog(self):
        if not self.editable or self.job:
            self.set_status("Make an editable copy to change a PDF or Word document.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Find and replace")
        form = QFormLayout(dialog)
        find, replacement = QLineEdit(self.find_input.text()), QLineEdit()
        form.addRow("Find", find)
        form.addRow("Replace with", replacement)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Apply).setText("Replace all")
        def replace():
            query = find.text()
            if not query:
                return
            cursor = self.editor.textCursor()
            cursor.beginEditBlock()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            count = 0
            while True:
                found = self.editor.document().find(query, cursor)
                if found.isNull():
                    break
                found.insertText(replacement.text())
                cursor.setPosition(found.position())
                count += 1
            cursor.endEditBlock()
            self.set_status(f"Replaced {count} occurrence(s)")
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(replace)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)
        dialog.exec()

    def update_markdown(self, *_):
        if self.tabs.currentIndex() == 1:
            self.markdown.setMarkdown(self.editor.toPlainText())

    def bookmark_key(self):
        return str(self.document.path.resolve()) if self.document.path else None

    def refresh_bookmarks(self):
        self.bookmarks.clear()
        for entry in self.state.value.get("bookmarks", {}).get(self.bookmark_key(), []):
            item = QListWidgetItem(entry["label"])
            item.setData(Qt.ItemDataRole.UserRole, entry["position"])
            self.bookmarks.addItem(item)

    def add_bookmark(self):
        key = self.bookmark_key()
        if not key:
            self.set_status("Save this note before adding a bookmark.")
            return
        text = self.editor.toPlainText()
        position = python_position(text, self.editor.textCursor().position())
        label = text[position:position + 65].replace("\n", " ").strip() or "End of document"
        marks = self.state.value.setdefault("bookmarks", {}).setdefault(key, [])
        marks.append({"label": label, "position": position})
        self.state.save()
        self.refresh_bookmarks()
        self.side_tabs.setCurrentIndex(2)
        self.set_status("Position bookmarked")

    def goto_bookmark(self, item):
        self.stop()
        self.parts = []
        self.current = 0
        self.set_cursor(item.data(Qt.ItemDataRole.UserRole))
        self.render_page()

    def remove_bookmark(self):
        row = self.bookmarks.currentRow()
        marks = self.state.value.get("bookmarks", {}).get(self.bookmark_key(), [])
        if 0 <= row < len(marks):
            marks.pop(row)
            self.state.save()
            self.refresh_bookmarks()

    def read_clipboard(self):
        if self.job:
            self.set_status("Finish or cancel the current document task first.")
            return
        text = QApplication.clipboard().text()
        if not text.strip():
            self.set_status("Copy some text first, then press Ctrl+Alt+R.")
            return
        if not self.confirm_unsaved():
            self.showNormal()
            self.activateWindow()
            return
        self.save_progress()
        self.apply_document(Document(None, [Page(text)], "Copied text"))
        self.parts = sentences(text)
        self.start_speech()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.job:
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            self.open_path(Path(urls[0].toLocalFile()))

    def show_guide(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Luma Reader · User guide")
        dialog.resize(820, 650)
        layout = QVBoxLayout(dialog)
        browser = QTextBrowser()
        browser.setMarkdown((ROOT / "USER_GUIDE.md").read_text(encoding="utf-8"))
        layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def about(self):
        QMessageBox.information(self, "About Luma Reader", "Luma Reader · local document reading and notes\n\nPiper speech · RapidOCR recognition · Qt interface\n\nDocuments, voices and OCR are processed locally. Inference telemetry is disabled by Luma.\n\nPiper: GPL-3.0-or-later. PyMuPDF: AGPL/commercial. PySide6: LGPL/GPL/commercial. See THIRD_PARTY.md and voice model cards before distributing. Luma is open source. See the included notices for dependency and voice credits.")

    def closeEvent(self, event):
        if self.job:
            if not self.close_pending:
                choice = QMessageBox.question(self, "Task in progress", "Cancel the current task and close when the current page or speech chunk finishes?")
                if choice != QMessageBox.StandardButton.Yes:
                    event.ignore()
                    return
                self.save_progress()
                self.close_pending = True
                self.cancel_job()
            event.ignore()
            return
        if not self.confirm_unsaved():
            self.close_pending = False
            event.ignore()
            return
        self.save_progress()
        self.speech.stop()
        if self.hotkey:
            self.hotkey.release()
            QApplication.instance().removeNativeEventFilter(self.hotkey)
        if self.pdf:
            self.pdf.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Luma Reader")
    app.setOrganizationName("Luma Local")
    DATA.mkdir(parents=True, exist_ok=True)
    from runtime_paths import migrate_legacy_data
    migrate_legacy_data(ROOT / 'data',DATA)
    lock = QLockFile(str(DATA / "luma.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(None, "Luma Reader is already open", "Use the existing Luma Reader window. Ctrl+Alt+R reads copied text while it is running.")
        return
    def report_error(kind, error, tb):
        import traceback
        with (DATA / "application.log").open("a", encoding="utf-8") as log:
            traceback.print_exception(kind, error, tb, file=log)
        QMessageBox.warning(None, "Luma Reader", f"An unexpected error occurred: {error}\n\nDetails are saved locally in {DATA / 'application.log'}.")
    sys.excepthook = report_error
    window = Reader()
    window.show()
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        QTimer.singleShot(0, lambda: window.open_path(Path(sys.argv[1])))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
