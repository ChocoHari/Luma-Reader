"""Rich editing with deliberately separate Markdown and plain-text modes."""
from PySide6.QtCore import Qt
from PySide6.QtGui import (QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat)
from PySide6.QtWidgets import (QColorDialog, QComboBox, QFontComboBox, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QTextEdit, QVBoxLayout, QWidget)


class NoteEditor(QTextEdit):
    def __init__(self):
        super().__init__()
        self.note_mode = "plain"
        self.setAcceptRichText(False)

    def setLineWrapMode(self, mode):
        super().setLineWrapMode(QTextEdit.LineWrapMode(mode.value))

    def centerCursor(self):
        self.ensureCursorVisible()
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + self.cursorRect().center().y() - self.viewport().height()//2)

    def merge_format(self, fmt):
        cursor = self.textCursor()
        cursor.mergeCharFormat(fmt)
        self.mergeCurrentCharFormat(fmt)

    def command(self, kind, value=None):
        if self.isReadOnly():
            return
        if self.note_mode == "markdown":
            self.markdown_command(kind, value)
            return
        if self.note_mode != "rich":
            return
        fmt = QTextCharFormat()
        current = self.currentCharFormat()
        if kind == "bold": fmt.setFontWeight(QFont.Weight.Normal if current.fontWeight() >= QFont.Weight.Bold else QFont.Weight.Bold)
        elif kind == "italic": fmt.setFontItalic(not current.fontItalic())
        elif kind == "underline": fmt.setFontUnderline(not current.fontUnderline())
        elif kind == "strike": fmt.setFontStrikeOut(not current.fontStrikeOut())
        elif kind in {"sub", "sup"}:
            alignment = QTextCharFormat.VerticalAlignment.AlignSubScript if kind == "sub" else QTextCharFormat.VerticalAlignment.AlignSuperScript
            fmt.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignNormal if current.verticalAlignment() == alignment else alignment)
        elif kind == "font": fmt.setFontFamilies([value])
        elif kind == "size": fmt.setFontPointSize(value)
        elif kind in {"color", "highlight"}:
            color = QColorDialog.getColor(parent=self)
            if not color.isValid(): return
            fmt.setForeground(color) if kind == "color" else fmt.setBackground(color)
        elif kind == "clear":
            cursor=self.textCursor()
            cursor.beginEditBlock()
            block=cursor.document().findBlock(cursor.selectionStart())
            end=cursor.selectionEnd()
            while block.isValid() and block.position()<=end:
                if block.textList():block.textList().remove(block)
                block=block.next()
            cursor.setCharFormat(QTextCharFormat())
            self.setCurrentCharFormat(QTextCharFormat())
            block = QTextBlockFormat()
            cursor.setBlockFormat(block)
            cursor.endEditBlock()
            return
        elif kind == "heading":
            cursor = self.textCursor()
            cursor.beginEditBlock()
            block = cursor.blockFormat()
            block.setHeadingLevel(int(value))
            block.setTopMargin(14 if value else 3)
            block.setBottomMargin(8)
            cursor.mergeBlockFormat(block)
            fmt.setFontWeight(QFont.Weight.Bold if value else QFont.Weight.Normal)
            fmt.setFontPointSize({0:14,1:26,2:21,3:17}[int(value)])
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.mergeCharFormat(fmt)
            cursor.endEditBlock()
            return
        elif kind in {"bullet", "number"}:
            listing = QTextListFormat()
            listing.setStyle(QTextListFormat.Style.ListDisc if kind == "bullet" else QTextListFormat.Style.ListDecimal)
            listing.setIndent(1)
            self.textCursor().createList(listing)
            return
        elif kind in {"indent", "outdent", "spacing"}:
            block = self.textCursor().blockFormat()
            if kind == "spacing":
                block.setBottomMargin(float(value))
            else:
                block.setIndent(max(0, block.indent() + (1 if kind == "indent" else -1)))
            self.textCursor().mergeBlockFormat(block)
            return
        elif kind == "align":
            self.setAlignment(value)
            return
        else:
            return
        self.merge_format(fmt)

    def markdown_command(self, kind, value):
        cursor = self.textCursor()
        selected = cursor.selectedText().replace("\u2029", "\n")
        wrappers = {"bold":"**", "italic":"*", "strike":"~~", "underline":"<u>", "sub":"<sub>", "sup":"<sup>"}
        if kind in wrappers:
            token = wrappers[kind]
            close = "</" + token[1:] if token.startswith("<") else token
            cursor.insertText(token + (selected or "text") + close)
        elif kind in {"heading", "bullet", "number", "task", "quote"}:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
            import re
            line = re.sub(r"^(?:#{1,6}\s+|[-*+]\s+|\d+\.\s+)", "", cursor.selectedText())
            prefix = "#"*int(value) + " " if kind == "heading" and value else ""
            prefix = "- " if kind == "bullet" else "1. " if kind == "number" else prefix
            if kind == "task": prefix = "- [ ] "
            if kind == "quote": prefix = "> "
            cursor.insertText(prefix + line)
        elif kind == "link": cursor.insertText("[" + (selected or "link text") + "](https://example.com)")
        elif kind == "code": cursor.insertText("`" + (selected or "code") + "`")
        elif kind == "codeblock": cursor.insertText("\n```\n" + (selected or "code") + "\n```\n")
        elif kind == "table": cursor.insertText("\n| Column 1 | Column 2 |\n| --- | --- |\n| Text | Text |\n")
        elif kind == "indent": cursor.insertText("    " + selected)
        elif kind == "clear":
            import re
            cursor.insertText(re.sub(r"[*_~`]|</?(?:u|sub|sup)>", "", selected))
        self.setTextCursor(cursor)


class FormatBar(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.command_buttons = {}
        self.setObjectName("formatBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(5)
        top, bottom = QHBoxLayout(), QHBoxLayout()
        self.style = QComboBox()
        self.style.addItems(["Paragraph", "Heading 1", "Heading 2", "Heading 3"])
        self.style.activated.connect(lambda index: editor.command("heading", index))
        top.addWidget(self.style)
        self.font = QFontComboBox()
        self.font.setMaximumWidth(180)
        self.font.activated.connect(lambda _: editor.command("font",self.font.currentFont().family()))
        top.addWidget(self.font)
        self.size = QSpinBox()
        self.size.setRange(8,72)
        self.size.setValue(14)
        self.size.valueChanged.connect(lambda size: editor.command("size",size))
        top.addWidget(self.size)
        self.toggles = {}
        for name, label, tip in [("bold","B","Bold · Ctrl+B"),("italic","I","Italic · Ctrl+I"),
                    ("underline","U","Underline · Ctrl+U"),("strike","S̶","Strikethrough"),
                    ("sub","x₂","Subscript"),("sup","x²","Superscript")]:
            button = self.add_button(top, label, name, tip)
            button.setCheckable(True)
            self.toggles[name] = button
        top.addStretch()
        for name,label,tip in [("bullet","• List","Bulleted list"),("number","1. List","Numbered list"),
                 ("indent","→","Indent"),("outdent","←","Outdent"),("color","A","Text colour"),
                 ("highlight","▰","Highlight colour"),("clear","Clear","Clear formatting")]:
            self.add_button(bottom,label,name,tip)
        self.align = QComboBox()
        self.align.addItems(["Left", "Centre", "Right"])
        self.align.activated.connect(lambda i: editor.command("align", [Qt.AlignmentFlag.AlignLeft,Qt.AlignmentFlag.AlignHCenter,Qt.AlignmentFlag.AlignRight][i]))
        bottom.addWidget(self.align)
        self.spacing = QComboBox()
        self.spacing.addItems(["Compact", "Comfortable", "Spacious"])
        self.spacing.setCurrentIndex(1)
        self.spacing.activated.connect(lambda i: editor.command("spacing",[0,8,16][i]))
        bottom.addWidget(self.spacing)
        plain = QPushButton("Paste plain")
        plain.setToolTip("Paste without source formatting · Ctrl+Shift+V")
        plain.clicked.connect(lambda: editor.insertPlainText(__import__("PySide6.QtWidgets",fromlist=["QApplication"]).QApplication.clipboard().text()))
        bottom.addWidget(plain)
        bottom.addStretch()
        layout.addLayout(top)
        layout.addLayout(bottom)
        editor.currentCharFormatChanged.connect(self.sync)
        editor.cursorPositionChanged.connect(lambda: self.sync(editor.currentCharFormat()))

    def add_button(self,row,label,kind,tip):
        button = QPushButton(label)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        button.clicked.connect(lambda _:self.editor.command(kind))
        row.addWidget(button)
        self.command_buttons[kind]=button
        return button

    def set_mode(self,mode):
        rich=mode=="rich"
        self.setEnabled(mode!="plain")
        for control in (self.font,self.size,self.align,self.spacing):control.setVisible(rich)
        for kind in ("color","highlight","outdent"):
            self.command_buttons[kind].setVisible(rich)
        for button in self.toggles.values():
            button.setCheckable(rich)
            if not rich:button.setChecked(False)

    def sync(self,fmt):
        values = {"bold":fmt.fontWeight()>=QFont.Weight.Bold,"italic":fmt.fontItalic(),
                  "underline":fmt.fontUnderline(),"strike":fmt.fontStrikeOut(),
                  "sub":fmt.verticalAlignment()==QTextCharFormat.VerticalAlignment.AlignSubScript,
                  "sup":fmt.verticalAlignment()==QTextCharFormat.VerticalAlignment.AlignSuperScript}
        for key,value in values.items():
            self.toggles[key].setChecked(value)
        self.style.blockSignals(True)
        self.style.setCurrentIndex(min(3,self.editor.textCursor().blockFormat().headingLevel()))
        self.style.blockSignals(False)
        for control in (self.font,self.size): control.blockSignals(True)
        if fmt.fontFamilies(): self.font.setCurrentFont(QFont(fmt.fontFamilies()[0]))
        if fmt.fontPointSize()>0:self.size.setValue(round(fmt.fontPointSize()))
        for control in (self.font,self.size): control.blockSignals(False)
        alignment=self.editor.alignment()
        self.align.setCurrentIndex(1 if alignment & Qt.AlignmentFlag.AlignHCenter else 2 if alignment & Qt.AlignmentFlag.AlignRight else 0)
