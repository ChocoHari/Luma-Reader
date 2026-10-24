"""V2 workspace features layered over the existing offline reader workflows."""
from __future__ import annotations
import json
import os
import re
import tempfile
import uuid
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QRectF, QUrl, QRect, QSize, QPoint
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap, QTextCursor, QTextDocument
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout, QHBoxLayout, QLayout, QWidgetItem, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget, QMenuBar, QSplitter, QListWidgetItem, QInputDialog)
from appearance import ASSETS, PALETTES, install_frame, logo_pixmap, place_edges, tokens
from rich_editor import FormatBar
from reader_core import DATA, ROOT, Document, Page, python_position, qt_position, sentences, atomic_json
from speech_text import margin_ranges, prepare_parts


class WrappingLayout(QLayout):
    """Keep toolbar controls reachable without imposing a single-row minimum."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setSpacing(8)

    def addWidget(self, widget, stretch=0):
        super().addWidget(widget)

    def addItem(self, item):
        self.items.append(item)
        self.invalidate()

    def insertWidget(self, index, widget):
        self.addChildWidget(widget)
        self.items.insert(index, QWidgetItem(widget))
        self.invalidate()

    def addStretch(self, stretch=0):
        pass

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        return self.items[index] if 0 <= index < len(self.items) else None

    def takeAt(self, index):
        return self.items.pop(index) if 0 <= index < len(self.items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self.arrange(QRect(0, 0, width, 0), False)

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            if not item.isEmpty():
                size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left()+margins.right(), margins.top()+margins.bottom())

    def sizeHint(self):
        return self.minimumSize()

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.arrange(rect, True)

    def arrange(self, rect, apply):
        margins = self.contentsMargins()
        area = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        x, y, row_height = area.x(), area.y(), 0
        for item in self.items:
            if item.isEmpty():
                continue
            size = item.sizeHint()
            if row_height and x + size.width() > area.right()+1:
                x, y, row_height = area.x(), y+row_height+self.spacing(), 0
            if apply:
                item.setGeometry(QRect(QPoint(x, y), size))
            x += size.width()+self.spacing()
            row_height = max(row_height, size.height())
        return y + row_height - rect.y() + margins.bottom()


class StudioFeatures:
    def nativeEvent(self,event_type,message):
        from window_frame import native_event
        result=native_event(self,message)
        return result if result is not None else super().nativeEvent(event_type,message)

    def menuBar(self):
        if not hasattr(self,"_studio_menu"):
            self._studio_menu=QMenuBar(self)
        return self._studio_menu

    def upgrade_ui(self):
        self.overlay_rects = []
        self.note_format = "plain"
        self.pdf_zoom = "Fit width"
        self._regions = {}
        self.profile = self.state.value.get("speech_profile","Natural")
        self.replacements = self.state.value.get("replacements",{})
        self.omit_margins = self.state.value.get("omit_margins",True)
        self._margin_cache = []
        self.setMinimumSize(760,560)
        install_frame(self)
        # V1's identity header is replaced by the custom title bar and compact command row.
        self.findChild(QWidget,"header").hide()
        main = self.content.parentWidget()
        layout = main.layout()
        commands = QWidget()
        row = WrappingLayout(commands)
        row.setContentsMargins(0,0,0,0)
        sidebar = self.splitter.widget(0)
        self.sidebar_button = self.button("☰", lambda:sidebar.setVisible(not sidebar.isVisible()))
        self.sidebar_button.setText("Menu")
        self.sidebar_button.setAccessibleName("Toggle document sidebar")
        row.addWidget(self.sidebar_button)
        self.workspace = QComboBox()
        self.workspace.addItems(["Read", "Write"])
        self.workspace.activated.connect(self.workspace_changed)
        row.addWidget(self.workspace)
        self.view_mode = QComboBox()
        self.view_mode.addItems(["PDF", "Split", "Text"])
        self.view_mode.currentTextChanged.connect(self.set_pdf_view)
        row.addWidget(self.view_mode)
        row.addWidget(self.button("Find",self.show_find))
        row.addStretch()
        row.addWidget(QLabel("Theme"))
        self.theme_box = QComboBox()
        self.theme_box.addItems(list(PALETTES))
        self.theme_box.setCurrentText(self.state.value.get("theme","Baby blue"))
        self.theme_box.currentTextChanged.connect(self.apply_theme)
        row.addWidget(self.theme_box)
        self.appearance_mode = QComboBox()
        self.appearance_mode.addItems(["Light", "Dark", "Windows"])
        self.appearance_mode.setCurrentText(self.state.value.get("appearance","Dark" if self.state.value.get("dark") else "Light"))
        self.appearance_mode.currentTextChanged.connect(self.apply_theme)
        row.addWidget(self.appearance_mode)
        row.addWidget(self.button("Settings",self.settings_dialog))
        layout.insertWidget(0,commands)
        self.format_bar = FormatBar(self.editor)
        layout.insertWidget(4,self.format_bar)
        self.markdown_split = QSplitter(Qt.Orientation.Horizontal)
        self.tabs.removeTab(0)
        self.markdown_split.addWidget(self.editor)
        self.split_preview = QTextBrowser()
        self.split_preview.setOpenLinks(False)
        self.split_preview.setOpenExternalLinks(False)
        self.markdown_split.addWidget(self.split_preview)
        self.tabs.insertTab(0,self.markdown_split,"Source")
        self.tabs.setCurrentIndex(0)
        self.split_preview.hide()
        self.markdown_view = QComboBox()
        self.markdown_view.addItems(["Source", "Preview", "Split"])
        self.markdown_view.currentTextChanged.connect(self.set_markdown_view)
        row.insertWidget(3,self.markdown_view)
        self.markdown_insert = QComboBox()
        self.markdown_insert.addItems(["Insert…", "Task", "Quote", "Link", "Code", "Code block", "Table"])
        self.markdown_insert.activated.connect(self.insert_markdown)
        row.insertWidget(4,self.markdown_insert)
        self.focus_button = self.button("Focus",self.toggle_writing_focus)
        self.focus_button.setCheckable(True)
        row.insertWidget(5,self.focus_button)
        self.markdown_refresh = QTimer(self)
        self.markdown_refresh.setSingleShot(True)
        self.markdown_refresh.setInterval(180)
        self.markdown_refresh.timeout.connect(self.refresh_markdown_workspace)
        self.editor.textChanged.connect(lambda:self.markdown_refresh.start())
        self._recovery_path = None
        self.recovery_timer = QTimer(self)
        self.recovery_timer.setSingleShot(True)
        self.recovery_timer.setInterval(2000)
        self.recovery_timer.timeout.connect(self.write_recovery)
        self.editor.textChanged.connect(lambda:self.recovery_timer.start())
        self.content.insertWidget(0,self.preview_scroll)
        self.preview_scroll.setObjectName("pdfSurface")
        from pdf_selection import PdfCanvas
        old_canvas=self.preview_scroll.takeWidget()
        self.preview_label=PdfCanvas()
        self.preview_scroll.setWidget(self.preview_label)
        old_canvas.deleteLater()
        self.pdf_selection_range=None
        self.pdf_selection_anchor=None
        self.preview_label.selectionStarted.connect(self.stop)
        self.preview_label.selectionMoved.connect(self.select_pdf_points)
        self.preview_label.copyRequested.connect(lambda:QApplication.clipboard().setText(self.editor.textCursor().selectedText().replace('\u2029','\n')))
        self.preview_label.readRequested.connect(self.read_selection)
        self.preview_label.fromHereRequested.connect(self.read_pdf_from_here)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.preview_label.setObjectName("pdfCanvas")
        self.content.setSizes([800,350])
        pdf_row = self.pdf_controls.layout()
        self.show_original.hide()
        self.zoom_box = QComboBox()
        self.zoom_box.addItems(["Fit width","Fit page","75%","100%","125%","150%","200%"])
        self.zoom_box.currentTextChanged.connect(self.zoom_changed)
        pdf_row.insertWidget(3,self.zoom_box)
        self.dim_page = QCheckBox("Dim page")
        self.dim_page.setChecked(self.state.value.get("dim_page",False))
        self.dim_page.toggled.connect(lambda _:self.render_page())
        pdf_row.insertWidget(4,self.dim_page)
        pdf_row.insertWidget(0,self.button("‹",lambda:self.goto_page(max(1,self.page_number.value()-1))))
        pdf_row.insertWidget(4,self.button("›",lambda:self.goto_page(min(self.page_number.maximum(),self.page_number.value()+1))))
        page_read = self.menuBar().addMenu("Page")
        self.action(page_read,"Read this page",self.read_page,"Ctrl+Shift+P")
        self.action(page_read,"Read from this page onward",self.read_from_page)
        self.action(page_read,"Previous page",lambda:self.goto_page(max(1,self.page_number.value()-1)),"Alt+Up")
        self.action(page_read,"Next page",lambda:self.goto_page(min(self.page_number.maximum(),self.page_number.value()+1)),"Alt+Down")
        self.action(page_read,"Zoom in",lambda:self.zoom_step(1),"Ctrl++")
        self.action(page_read,"Zoom out",lambda:self.zoom_step(-1),"Ctrl+-")
        edit_menu = self.menuBar().actions()[1].menu()
        for name,kind,key in [("Bold","bold","Ctrl+B"),("Italic","italic","Ctrl+I"),("Underline","underline","Ctrl+U")]:
            self.action(edit_menu,name,lambda checked=False,k=kind:self.editor.command(k),key)
        self.action(edit_menu,"Paste as plain text",lambda:self.editor.insertPlainText(QApplication.clipboard().text()),"Ctrl+Shift+V")
        self.action(edit_menu,"Convert note to rich format",self.convert_rich)
        self.action(self.menuBar().actions()[2].menu(),"Preview spoken text",self.spoken_preview,"Ctrl+Shift+T")
        self.action(self.menuBar().actions()[0].menu(),"New Markdown note",self.new_markdown)
        self.action(self.menuBar().actions()[0].menu(),"New plain text note",self.new_plain)
        self.action(self.menuBar().actions()[0].menu(),"Recover a draft…",self.recover_draft)
        self.action(self.menuBar().actions()[4].menu(),"Design and logo gallery",self.design_gallery)
        self.title.setMaximumHeight(36)
        self.title.setWordWrap(False)
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.system_theme = QApplication.styleHints()
        self.system_theme.colorSchemeChanged.connect(lambda *_:self.apply_theme())
        place_edges(self)

    def update_compact_workspace(self):
        # The title remains in the window caption; preserve document space on
        # short displays instead of squeezing the editor between fixed toolbars.
        compact = self.height() < 800
        focused = self.focus_button.isChecked()
        self.title.setVisible(not compact and not focused)
        self.meta.setVisible(not compact and not focused)
        layout = self.content.parentWidget().layout()
        layout.setContentsMargins(12 if compact else 28, 8 if compact else 22,
                                  12 if compact else 28, 8 if compact else 18)
        layout.setSpacing(6 if compact else 12)
        for index in range(self.reading_tools.count()):
            widget = self.reading_tools.itemAt(index).widget()
            if widget is not None:
                widget.setVisible(not focused and (widget is not self.draft_button or not self.editable))
        self.content.setMinimumHeight(140)

    def apply_theme(self,*_):
        if not hasattr(self,"theme_box"):
            return self._base_apply_theme()
        mode = self.appearance_mode.currentText()
        dark = mode == "Dark" or (mode=="Windows" and QApplication.styleHints().colorScheme()==Qt.ColorScheme.Dark)
        self.dark.blockSignals(True)
        self.dark.setChecked(dark)
        self.dark.blockSignals(False)
        t = tokens(self.theme_box.currentText(),dark)
        self.theme_tokens = t
        self.setStyleSheet(f"""
          QWidget {{ font-family:'Segoe UI'; font-size:13px; color:{t['text']}; background:{t['bg']}; }}
          QMainWindow {{ border:1px solid {t['border']}; }}
          QMenuBar,QMenu,QDialog {{ background:{t['panel']}; }}
          QMenuBar::item:selected,QMenu::item:selected {{ background:{t['tint']}; }}
          #titleBar {{ background:{t['panel']}; border-bottom:1px solid {t['border']}; }}
          #windowCaption {{ background:transparent; color:{t['muted']}; font-size:12px; }}
          #windowControl,#windowClose {{ border:none; background:transparent; font-size:20px; padding:0; }}
          #windowControl:hover {{ background:{t['tint']}; }}
          #windowClose:hover {{ background:#b83f4b; color:white; }}
          #sidebar,#playback,#formatBar {{ background:{t['panel']}; border:1px solid {t['border']}; }}
          #sidebar QLabel,#playback QLabel,#titleBar QLabel {{ background:transparent; }}
          #documentTitle {{ font-size:22px; font-weight:600; }}
          #muted {{ color:{t['muted']}; font-size:12px; }}
          QPushButton {{ background:{t['panel']}; border:1px solid {t['border']}; border-radius:7px; padding:7px 11px; }}
          QPushButton:hover,QPushButton:checked {{ background:{t['tint']}; border-color:{t['accent']}; }}
          QPushButton:focus,QComboBox:focus,QLineEdit:focus,QSpinBox:focus {{ border:2px solid {t['accent']}; }}
          QPushButton:disabled {{ color:{t['muted']}; }}
          #primary {{ background:{t['button']}; color:white; border-color:{t['button']}; font-weight:600; }}
          QComboBox,QSpinBox,QDoubleSpinBox,QLineEdit {{ background:{t['panel']}; border:1px solid {t['border']}; border-radius:6px; padding:5px; min-height:23px; }}
          QTextEdit,QPlainTextEdit,QTextBrowser {{ background:{t['panel']}; border:1px solid {t['border']}; border-radius:9px; padding:22px; selection-background-color:{t['tint']}; }}
          QListWidget,QTableWidget {{ background:{t['panel']}; border:none; outline:none; }}
          QListWidget::item {{ padding:9px 5px; border-radius:4px; }}
          QListWidget::item:selected {{ background:{t['tint']}; color:{t['text']}; }}
          QTabWidget::pane {{ border:none; }}
          QTabBar::tab {{ padding:7px 10px; color:{t['muted']}; }}
          QTabBar::tab:selected {{ color:{t['accent']}; border-bottom:2px solid {t['accent']}; }}
          QScrollArea {{ border:1px solid {t['border']}; border-radius:9px; }}
          #pdfSurface,#pdfCanvas {{ background:{'#131923' if dark else '#e5eaf1'}; }}
          QProgressBar {{ border:1px solid {t['border']}; border-radius:5px; text-align:center; min-height:22px; }}
          QProgressBar::chunk {{ background:{t['tint']}; }}
          QSplitter::handle {{ background:{t['border']}; width:4px; }}
          QToolTip {{ background:{t['panel']}; color:{t['text']}; border:1px solid {t['border']}; padding:6px; }}
        """)
        self.title_bar.mark.setPixmap(logo_pixmap(27,t['accent']))
        self.setWindowIcon(QIcon(logo_pixmap(64,t['accent'])))
        if self.pdf: self.render_page()

    def workspace_changed(self,index):
        if index==1 and not self.editable:
            self.make_draft()
        elif index==0 and self.pdf:
            self.view_mode.setCurrentText("PDF")

    def insert_markdown(self,index):
        commands = [None,"task","quote","link","code","codeblock","table"]
        if index and self.note_format=="markdown":
            self.editor.command(commands[index])
        self.markdown_insert.setCurrentIndex(0)

    def toggle_writing_focus(self):
        focused=self.focus_button.isChecked()
        if focused:
            self._focus_sidebar_visible=self.splitter.widget(0).isVisible()
        self.splitter.widget(0).setVisible(False if focused else getattr(self,"_focus_sidebar_visible",True))
        self.format_bar.setVisible(self.editable and not focused)
        self.focus_button.setText("Exit focus" if focused else "Focus")
        self.update_compact_workspace()

    def write_recovery(self):
        if not self.editable or not self.editor.document().isModified() or self._updating:return
        if self._recovery_path is None:
            self._recovery_path=DATA / "recovery" / (uuid.uuid4().hex+".json")
        try:
            atomic_json(self._recovery_path,{
                "schema_version":1,"title":self.document.title,"format":self.note_format,
                "text":self.editor.toHtml() if self.note_format=="rich" else self.editor.toPlainText(),
                "cursor":self.editor.textCursor().position()})
        except OSError:
            self.set_status("Draft recovery could not be saved. Please save your note.")

    def clear_recovery(self):
        self.recovery_timer.stop()
        if self._recovery_path:
            try:self._recovery_path.unlink(missing_ok=True)
            except OSError:pass
        self._recovery_path=None

    def confirm_unsaved(self):
        if not self.editor.document().isModified():return True
        choice=QMessageBox.question(self,"Save your note?","This note has unsaved changes.",
            QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save)
        if choice==QMessageBox.StandardButton.Save:return self.save()
        if choice==QMessageBox.StandardButton.Discard:
            self.clear_recovery()
            return True
        return False

    def recover_draft(self):
        drafts=[]
        for path in sorted((DATA / "recovery").glob("*.json"),key=lambda p:p.stat().st_mtime,reverse=True):
            try:
                value=json.loads(path.read_text(encoding="utf-8"))
                if value.get("schema_version")==1 and value.get("format") in {"markdown","plain","rich"} and isinstance(value.get("text"),str):
                    drafts.append((path,value))
            except (OSError,ValueError):continue
        if not drafts:
            self.set_status("No recovery drafts are available.")
            return
        labels=[f"{i+1}. {v.get('title','Untitled note')}" for i,(_,v) in enumerate(drafts)]
        chosen,ok=QInputDialog.getItem(self,"Recover a draft","Choose a local recovery draft:",labels,0,False)
        if not ok or not self.confirm_unsaved():return
        path,value=drafts[labels.index(chosen)]
        fmt=value["format"]
        doc=Document(None,[Page(value["text"] if fmt!="rich" else "")],value.get("title","Recovered note"))
        if fmt=="rich":doc.rich_html=value["text"]
        self.apply_document(doc,restore=False)
        self.note_format=self.editor.note_mode=fmt
        self.editor.setAcceptRichText(fmt=="rich")
        self.sync_note_controls()
        cursor=self.editor.textCursor()
        cursor.setPosition(min(max(0,int(value.get("cursor",0))),self.editor.document().characterCount()-1))
        self.editor.setTextCursor(cursor)
        self._recovery_path=path
        self.editor.document().setModified(True)
        self.set_status("Recovered draft · save it to keep a document copy.")

    def sync_note_controls(self):
        markdown=self.note_format=="markdown"
        self.markdown_view.setVisible(markdown)
        self.markdown_insert.setVisible(markdown)
        self.tabs.setTabVisible(1,markdown)
        self.split_preview.hide()
        self.editor.show()
        self.markdown_split.setSizes([1000,0])
        self.format_bar.set_mode(self.note_format)
        self.format_bar.setVisible(self.editable and not self.focus_button.isChecked())
        self.tabs.setTabText(0,"Markdown source" if markdown else "Rich note" if self.note_format=="rich" else "Text")
        if markdown:self.set_markdown_view(self.markdown_view.currentText())
        else:self.tabs.setCurrentIndex(0)

    def set_markdown_view(self,view):
        if self.note_format!="markdown":return
        self.split_preview.setVisible(view=="Split")
        self.editor.show()
        self.markdown_split.setSizes([max(300,self.tabs.width()//2),max(300,self.tabs.width()//2)] if view=="Split" else [1000,0])
        self.tabs.setCurrentIndex(1 if view=="Preview" else 0)
        self.refresh_markdown_workspace()

    def refresh_markdown_workspace(self):
        if self.note_format!="markdown":return
        text=self.editor.toPlainText()
        self.split_preview.setMarkdown(text)
        self.markdown.setMarkdown(text)
        self.outline.clear()
        fenced=False
        offset=0
        for line in text.splitlines(keepends=True):
            if re.match(r"^\s*(```|~~~)",line):fenced=not fenced
            match=re.match(r"^(#{1,6})\s+(.+?)\s*$",line) if not fenced else None
            if match:
                item=QListWidgetItem("  "*(len(match[1])-1)+match[2])
                item.setData(Qt.ItemDataRole.UserRole,("offset","",offset))
                self.outline.addItem(item)
            offset+=len(line)

    def apply_document(self,document,restore=True):
        self._recovery_path=None
        self.pdf_selection_range=None
        self.pdf_selection_anchor=None
        self._base_apply_document(document,restore)
        suffix = document.path.suffix.lower() if document.path else ""
        self.note_format = "rich" if document.rich_html or suffix in {".html",".htm"} else "markdown" if suffix in {".md",".markdown"} or (document.path is None and document.title!="Welcome") else "plain"
        self.editable = self.editable or suffix in {".html",".htm"}
        self.editor.note_mode = self.note_format
        self.editor.setAcceptRichText(self.note_format=="rich")
        self.editor.setReadOnly(not self.editable)
        self.editor.setUndoRedoEnabled(self.editable)
        if document.rich_html:
            self._updating = True
            self.editor.setHtml(document.rich_html)
            document.pages = [Page(self.editor.toPlainText())]
            self.editor.document().setModified(False)
            self._updating = False
            if restore and document.path:
                self.set_cursor(self.state.value.get("positions",{}).get(str(document.path.resolve()),0))
        self._margin_cache = margin_ranges(document)
        self._regions = {}
        self.overlay_rects = []
        self.format_bar.setVisible(self.editable)
        self.format_bar.setEnabled(self.editable and self.note_format!="plain")
        self.workspace.blockSignals(True)
        self.workspace.setCurrentIndex(1 if self.editable else 0)
        self.workspace.blockSignals(False)
        self.view_mode.setVisible(bool(self.pdf))
        self.pdf_controls.setVisible(bool(self.pdf))
        if self.pdf:
            self.set_pdf_view(self.state.value.get("pdf_view","PDF"))
            self.view_mode.setCurrentText(self.state.value.get("pdf_view","PDF"))
            self.side_tabs.setCurrentIndex(1)
        else:
            self.preview_scroll.hide()
            self.tabs.show()
        self.tabs.setTabVisible(1,self.note_format=="markdown")
        self.tabs.setTabText(0,"Rich note" if self.note_format=="rich" else "Markdown source" if self.note_format=="markdown" else "Text")
        self.sync_note_controls()
        self.update_compact_workspace()
        self.update_title()
        QTimer.singleShot(0,self.render_page)

    def update_title(self,*_):
        self._base_update_title()
        if not hasattr(self,"note_format"): return
        title = self.document.title
        self.title.setToolTip(title)
        self.title.setText(title if len(title)<85 else title[:81]+"…")
        label = "Rich note · HTML preserves formatting" if self.note_format=="rich" else "Markdown source" if self.note_format=="markdown" else "Plain text" if self.editable else "Original document · offline reading"
        self.meta.setText(f"{len(self.editor.toPlainText().split()):,} words  ·  {label}")

    def set_pdf_view(self,view):
        if not self.pdf:return
        self.preview_scroll.setVisible(view!="Text")
        self.tabs.setVisible(view!="PDF")
        self.content.setSizes([850,450] if view=="Split" else [1000,0])
        QTimer.singleShot(0,self.render_page)

    def zoom_changed(self,value):
        self.pdf_zoom = value
        self.render_page()

    def zoom_step(self,step):
        choices=["75%","100%","125%","150%","200%"]
        index=choices.index(self.pdf_zoom) if self.pdf_zoom in choices else 1
        self.zoom_box.setCurrentText(choices[max(0,min(4,index+step))])

    def render_page(self):
        if not self.pdf or not self.preview_scroll.isVisible():return
        import pymupdf as fitz
        page = self.pdf[self.page_number.value()-1]
        viewport=self.preview_scroll.viewport()
        zoom=getattr(self,"pdf_zoom","Fit width")
        if zoom=="Fit page":scale=min(max(100,viewport.width()-28)/page.rect.width,max(100,viewport.height()-28)/page.rect.height)
        elif zoom.endswith("%"):
            scale=float(zoom[:-1])/100*96/72
        else:scale=max(200,viewport.width()-28)/page.rect.width
        # Prevent excessive render sizes at high DPI or unusually large page dimensions.
        scale=min(scale,4500/max(page.rect.width,page.rect.height))
        pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
        image=QPixmap()
        image.loadFromData(pix.tobytes("png"))
        painter=QPainter(image)
        if hasattr(self,"dim_page") and self.dim_page.isChecked():
            painter.fillRect(image.rect(),QColor(30,25,35,65))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(240,193,72,95))
        for x0,y0,x1,y1 in getattr(self,"overlay_rects",[]):
            painter.drawRoundedRect(QRectF(x0*scale,y0*scale,(x1-x0)*scale,(y1-y0)*scale),2,2)
        if getattr(self,'pdf_selection_range',None):
            a,b=self.pdf_selection_range
            page_start=self.document.page_start(self.page_number.value()-1)
            a,b=a-page_start,b-page_start
            painter.setBrush(QColor(70,140,225,95))
            for start,end,rect in self.pdf_page_regions():
                if start<b and end>a:
                    x0,y0,x1,y1=rect
                    painter.drawRect(QRectF(x0*scale,y0*scale,(x1-x0)*scale,(y1-y0)*scale))
        painter.end()
        self.preview_label.setPixmap(image)
        self.preview_label.setMinimumSize(image.size())
        self.preview_label.setToolTip(f"Page {self.page_number.value()} · {self.document.pages[self.page_number.value()-1].method}")

    def pdf_page_regions(self):
        index=self.page_number.value()-1
        source=self.document.pages[index]
        if 'OCR' in source.method:
            return [(r['start'],r['end'],r['rect']) for r in source.regions]
        if index not in self._regions:
            from types import SimpleNamespace
            start=self.document.page_start(index)
            self.sentence_rectangles(SimpleNamespace(start=start,end=start+len(source.text)))
        regions=self._regions.get(index,[])
        expected=len(re.findall(r'\w+',source.text))
        if expected and len(regions)/expected<.8:return []
        page=self.pdf[index]
        if page.rotation:
            import pymupdf
            return [(a,b,list(pymupdf.Rect(rect)*page.rotation_matrix)) for a,b,rect in regions]
        return regions

    def read_pdf_from_here(self):
        cursor=self.editor.textCursor()
        cursor.setPosition(cursor.selectionStart())
        self.editor.setTextCursor(cursor)
        self.read_cursor()

    def select_pdf_points(self,anchor,position):
        if not self.pdf:return
        from pdf_selection import nearest_region
        pix=self.preview_label.pixmap()
        if not pix or pix.isNull():return
        page=self.pdf[self.page_number.value()-1]
        scale=pix.width()/page.rect.width
        offset=max(0,(self.preview_label.width()-pix.width())/2)
        regions=self.pdf_page_regions()
        first=nearest_region(regions,(anchor.x()-offset)/scale,anchor.y()/scale)
        last=nearest_region(regions,(position.x()-offset)/scale,position.y()/scale)
        if first is None or last is None:
            self.set_status('This page needs OCR coordinates before direct text selection is available.')
            return
        a,b=min(first[0],last[0]),max(first[1],last[1])
        source=self.document.pages[self.page_number.value()-1].text
        while b<len(source) and source[b] in '.,;:!?\u201d\u2019\")':b+=1
        start=self.document.page_start(self.page_number.value()-1)
        if self.preview_label.extend_selection and self.pdf_selection_anchor is not None:
            fixed=self.pdf_selection_anchor
            a,b=min(fixed,start+last[0]),max(fixed,start+b)
        else:
            self.pdf_selection_anchor=start+first[0]
            a,b=start+a,start+b
        self.pdf_selection_range=(a,b)
        text=self.editor.toPlainText()
        cursor=self.editor.textCursor()
        cursor.setPosition(qt_position(text,a))
        cursor.setPosition(qt_position(text,b),QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.render_page()

    def goto_page(self,number):
        if not self.pdf:return
        number=max(1,min(len(self.document.pages),number))
        self.overlay_rects=[]
        self._base_goto_page(number)
        if self.pdf_selection_range:
            text=self.editor.toPlainText()
            a,b=self.pdf_selection_range
            cursor=self.editor.textCursor()
            cursor.setPosition(qt_position(text,a))
            cursor.setPosition(qt_position(text,b),QTextCursor.MoveMode.KeepAnchor)
            self.editor.setTextCursor(cursor)
            self.render_page()
        self.preview_scroll.verticalScrollBar().setValue(0)

    def read_page(self):
        if not self.pdf:return
        page=self.page_number.value()-1
        start=self.document.page_start(page)
        self.parts=sentences(self.editor.toPlainText(),start,start+len(self.document.pages[page].text))
        self.start_speech()

    def read_from_page(self):
        if not self.pdf:return
        start=self.document.page_start(self.page_number.value()-1)
        self.parts=sentences(self.editor.toPlainText(),start)
        self.start_speech()

    def prepare_speech(self,parts):
        text=self.editor.toPlainText()
        if self.note_format=="rich":
            from bisect import bisect_right,bisect_left
            boundaries=[]
            block=self.editor.document().begin()
            headings=[]
            offset=0
            while block.isValid():
                boundaries.append(offset)
                if block.blockFormat().headingLevel():headings.append(offset)
                offset+=len(block.text())+1
                block=block.next()
            split=[]
            for part in parts:
                points=[part.start]+boundaries[bisect_right(boundaries,part.start):bisect_left(boundaries,part.end)]+[part.end]
                for a,b in zip(points,points[1:]):split.extend(sentences(text,a,b))
            parts=split
        result=prepare_parts(text,parts,self.profile,self.replacements,
            self.note_format=="markdown",self._margin_cache if self.omit_margins and self.profile!="Literal" else ())
        if self.note_format=="rich" and self.profile=="Study":
            for part in result:
                if part.start in headings:part.pause_after=.6
        return result

    def start_speech(self,index=0):
        if not getattr(self,"testing_voice",False):
            old_start=self.parts[min(index,len(self.parts)-1)].start if self.parts else 0
            self.parts=self.prepare_speech(self.parts)
            index=next((i for i,p in enumerate(self.parts) if p.end>old_start),0)
        self._base_start_speech(index)

    def stop(self):
        self._base_stop()
        self.overlay_rects=[]
        if hasattr(self,"preview_scroll") and self.pdf:self.render_page()

    def reading_finished(self):
        self._base_reading_finished()
        self.overlay_rects=[]
        self.render_page()

    def highlight(self,index):
        self._base_highlight(index)
        if self.pdf and not getattr(self,"testing_voice",False):
            self.overlay_rects=self.sentence_rectangles(self.parts[index])
            self.render_page()
            if self.overlay_rects:
                page=self.pdf[self.page_number.value()-1]
                pix=self.preview_label.pixmap()
                scale=pix.width()/page.rect.width if pix else 1
                y=self.overlay_rects[0][1]*scale
                self.preview_scroll.verticalScrollBar().setValue(max(0,int(y-self.preview_scroll.viewport().height()*.35)))

    def sentence_rectangles(self,part):
        index=self.page_number.value()-1
        source=self.document.pages[index]
        start=self.document.page_start(index)
        left,right=part.start-start,part.end-start
        if "OCR" in source.method:
            return [r["rect"] for r in source.regions if r["start"]<right and r["end"]>left]
        # Source-to-word alignment is lazy, cached per page, and must be confident.
        if index not in self._regions:
            from difflib import SequenceMatcher
            from pdf_reading_order import native_page_content
            _,words,_=native_page_content(self.pdf[index])
            tokens=list(re.finditer(r"\w+",source.text))
            spatial=[]
            for word in words:
                spatial.extend((m.group().casefold(),list(word[:4])) for m in re.finditer(r"\w+",word[4]))
            matcher=SequenceMatcher(None,[m.group().casefold() for m in tokens],[w[0] for w in spatial],autojunk=False)
            regions=[]
            for block in matcher.get_matching_blocks():
                for delta in range(block.size):
                    token=tokens[block.a+delta]
                    regions.append((token.start(),token.end(),spatial[block.b+delta][1]))
            self._regions[index]=regions
        regions=[r for r in self._regions[index] if r[0]<right and r[1]>left]
        expected=len(re.findall(r"\w+",source.text[max(0,left):right]))
        rects=[r[2] for r in regions] if expected and len(regions)/expected>=.8 else []
        page=self.pdf[index]
        if page.rotation:
            import pymupdf
            rects=[list(pymupdf.Rect(rect)*page.rotation_matrix) for rect in rects]
        return rects

    def spoken_preview(self):
        text=self.editor.toPlainText()
        cursor=self.editor.textCursor()
        start,end=(python_position(text,cursor.selectionStart()),python_position(text,cursor.selectionEnd())) if cursor.hasSelection() else (0,len(text))
        parts=self.prepare_speech(sentences(text,start,end))
        dialog=QDialog(self)
        dialog.setWindowTitle(f"Spoken text · {self.profile}")
        dialog.resize(740,580)
        layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel("This is the text sent to Piper. The original document is unchanged."))
        preview=QTextBrowser()
        preview.setPlainText("\n\n".join(p.spoken for p in parts))
        layout.addWidget(preview)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()

    def settings_dialog(self):
        dialog=QDialog(self)
        dialog.setWindowTitle("Luma settings · speech")
        dialog.resize(680,540)
        layout=QVBoxLayout(dialog)
        form=QFormLayout()
        standard_frame=QCheckBox("Use the standard Windows title bar (after restarting Luma)")
        standard_frame.setChecked(self.state.value.get("standard_frame",False))
        form.addRow(standard_frame)
        profile=QComboBox()
        profile.addItems(["Natural","Study","Literal"])
        profile.setCurrentText(self.profile)
        form.addRow("Reading profile",profile)
        omit=QCheckBox("Omit repeated PDF margin lines and page numbers")
        omit.setChecked(self.omit_margins)
        form.addRow(omit)
        explanation=QLabel("Natural skips decorative lines and turns arrows into pauses. Study speaks arrows and notation. Literal preserves more symbols. All run offline.")
        explanation.setWordWrap(True)
        form.addRow(explanation)
        layout.addLayout(form)
        layout.addWidget(QLabel("Pronunciation and replacement dictionary · whole terms, case insensitive"))
        table=QTableWidget(0,2)
        table.setHorizontalHeaderLabels(["Written term","Speak as"])
        table.horizontalHeader().setStretchLastSection(True)
        for term,replacement in self.replacements.items():
            row=table.rowCount();table.insertRow(row)
            table.setItem(row,0,QTableWidgetItem(term));table.setItem(row,1,QTableWidgetItem(replacement))
        layout.addWidget(table)
        row=QHBoxLayout()
        row.addWidget(self.button("Add term",lambda:table.insertRow(table.rowCount())))
        row.addWidget(self.button("Remove selected term",lambda:table.removeRow(table.currentRow()) if table.currentRow()>=0 else None))
        row.addStretch();layout.addLayout(row)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            self.state.value["standard_frame"]=standard_frame.isChecked()
            self.stop()
            self.profile=profile.currentText();self.omit_margins=omit.isChecked()
            self.replacements={table.item(r,0).text().strip():table.item(r,1).text() if table.item(r,1) else "" for r in range(table.rowCount()) if table.item(r,0) and table.item(r,0).text().strip()}
            self.save_progress()
            self.set_status("Speech preferences saved · use Read → Preview spoken text to review them.")

    def new_markdown(self):
        self.new_note()
        if self.document.path is None and self.document.title=="Untitled note":
            self.note_format=self.editor.note_mode="markdown"
            self.editor.setAcceptRichText(False)
            self.tabs.setTabVisible(1,True)
            self.tabs.setTabText(0,"Markdown source")
            self.sync_note_controls()
            self.update_title()

    def new_plain(self):
        self.new_note()
        if self.document.path is None and self.document.title=="Untitled note":
            self.note_format=self.editor.note_mode="plain"
            self.editor.setAcceptRichText(False)
            self.format_bar.setEnabled(False)
            self.sync_note_controls()
            self.update_title()

    def convert_rich(self):
        if not self.editable:return
        text=self.editor.toPlainText()
        if self.note_format=="markdown":
            self._updating=True
            self.editor.setMarkdown(text)
            self._updating=False
        self.note_format=self.editor.note_mode="rich"
        self.editor.setAcceptRichText(True)
        self.document.path=None
        self.document.title="Converted rich note"
        self.format_bar.setEnabled(True)
        self.tabs.setCurrentIndex(0);self.tabs.setTabVisible(1,False)
        self.sync_note_controls()
        self.editor.document().setModified(True)
        self.update_title()

    def make_draft(self):
        source_headings=list(self.document.headings)
        self._base_make_draft()
        if self.document.path is None and self.document.title=="Editable copy":
            cursor=self.editor.textCursor()
            cursor.beginEditBlock()
            block=self.editor.document().begin()
            while block.isValid():
                label=block.text().strip()
                if any(label==title.strip() for title,_ in source_headings):
                    cursor.setPosition(block.position())
                    self.editor.setTextCursor(cursor)
                    self.editor.command("heading",1)
                block=block.next()
            cursor.endEditBlock()

    def save(self,save_as=False):
        if self.job:return False
        path=self.document.path
        rich=self.note_format=="rich"
        if save_as or path is None or not self.editable:
            default="note.html" if rich else "note.md" if self.note_format=="markdown" else "note.txt"
            from runtime_paths import EXPORT_ROOT
            selected,_=QFileDialog.getSaveFileName(self,"Save note" if self.editable else "Export reading text",str(EXPORT_ROOT/default),
                "Rich note (*.html);;Markdown (*.md);;Text (*.txt)" if rich else "Markdown (*.md);;Text (*.txt);;Rich note (*.html)")
            if not selected:return False
            path=Path(selected)
            if not path.suffix:path=path.with_suffix(".html" if rich else ".md" if self.note_format=="markdown" else ".txt")
        suffix=path.suffix.lower()
        if suffix not in {".html",".htm",".md",".markdown",".txt"}:
            self.error("Save a rich note as HTML, a Markdown note as MD, or plain text as TXT.")
            return False
        if rich and suffix not in {".html",".htm"}:
            reply=QMessageBox.question(self,"Formatting conversion","TXT cannot retain formatting. Markdown preserves only its supported formatting; colours, alignment and spacing can be lost. Continue saving this converted copy?",
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
            if reply!=QMessageBox.StandardButton.Yes:return False
        content=self.editor.toHtml() if suffix in {".html",".htm"} else self.editor.toMarkdown() if rich and suffix in {".md",".markdown"} else self.editor.toPlainText()
        if self.note_format=="markdown" and suffix in {".html",".htm"}:
            rendered=QTextDocument()
            rendered.setMarkdown(self.editor.toPlainText())
            content=rendered.toHtml()
        try:
            fd,temp=tempfile.mkstemp(dir=path.parent,suffix=".tmp")
            try:
                with os.fdopen(fd,"w",encoding="utf-8",newline="") as stream:stream.write(content)
                os.replace(temp,path)
            finally:Path(temp).unlink(missing_ok=True)
        except OSError as error:
            self.error(str(error));return False
        if not self.editable:
            self.set_status(f"Exported reading text as {path.name}. The source document is unchanged.")
            return True
        # Lossy exports do not discard the current rich note or mark it saved.
        if rich and suffix not in {".html",".htm"}:
            self.set_status(f"Exported {path.name}. The rich note remains open; save it as HTML to retain all formatting.")
            return False if self.editor.document().isModified() else True
        self.document.path=path;self.document.title=path.name
        if self.note_format=="markdown" and suffix in {".html",".htm"}:
            self._updating=True
            self.editor.setHtml(content)
            self._updating=False
        self.note_format=self.editor.note_mode="rich" if suffix in {".html",".htm"} else "markdown" if suffix in {".md",".markdown"} else "plain"
        self.editor.setAcceptRichText(self.note_format=="rich")
        self.format_bar.setEnabled(self.note_format!="plain")
        self.document.rich_html=content if self.note_format=="rich" else None
        self.document.pages=[Page(self.editor.toPlainText())]
        self.editor.document().setModified(False)
        self.clear_recovery()
        self.sync_note_controls()
        self.state.remember(path,python_position(self.editor.toPlainText(),self.editor.textCursor().position()))
        self.refresh_recent();self.update_title()
        self.tabs.setTabVisible(1,self.note_format=="markdown")
        self.set_status(f"Saved {path.name}")
        return True

    def save_progress(self):
        if hasattr(self,"theme_box"):
            self.state.value.update(theme=self.theme_box.currentText(),appearance=self.appearance_mode.currentText(),
                speech_profile=self.profile,replacements=self.replacements,omit_margins=self.omit_margins,
                pdf_view=self.view_mode.currentText(),dim_page=self.dim_page.isChecked())
        self._base_save_progress()

    def design_gallery(self):
        dialog=QDialog(self);dialog.setWindowTitle("Luma · identity and themes");dialog.resize(900,660)
        layout=QVBoxLayout(dialog)
        browser=QTextBrowser()
        # Generate from the shipped identity instead of relying on a private design-board file.
        html=['<h1>Luma Reader · identity and themes</h1><p>Book & wave is Luma’s selected identity.</p><table cellpadding="14"><tr>']
        for concept,label in (('book-wave','Book & wave'),('page-sound','Page & sound'),('luma-orbit','Luma orbit')):
            browser.document().addResource(QTextDocument.ResourceType.ImageResource,QUrl(concept),logo_pixmap(80,concept=concept))
            html.append(f'<td><img src="{concept}" width="80" height="80"><p>{label}</p></td>')
        html.append('</tr></table><h2>Light and dark themes</h2><table cellpadding="18">')
        for name in PALETTES:
            html.append('<tr>')
            for dark in (False,True):
                palette=tokens(name,dark)
                html.append(f'<td bgcolor="{palette["bg"]}"><font color="{palette["text"]}"><b>{name} · {"Dark" if dark else "Light"}</b><p>A quieter place to read.</p></font></td>')
            html.append('</tr>')
        html.append('</table>')
        browser.setHtml(''.join(html))
        layout.addWidget(browser)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject);layout.addWidget(buttons);dialog.exec()
