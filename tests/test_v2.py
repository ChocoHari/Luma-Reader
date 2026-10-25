import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
from pathlib import Path
import pytest
import reader_core as core
from speech_text import prepare_parts,spoken_text,margin_ranges

@pytest.fixture(scope="module")
def application():
    from PySide6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    return app

@pytest.fixture
def window(tmp_path,monkeypatch,application):
    import studio
    monkeypatch.setattr(core,"DATA",tmp_path/"state")
    monkeypatch.setattr(studio,"DATA",tmp_path/"state")
    from app import Reader
    w=Reader(register_hotkey=False)
    w.show();application.processEvents()
    yield w
    w.editor.document().setModified(False)
    w.close();application.processEvents()


def test_titles_initialisms_decimals_and_source_mapping():
    text="Mr. Brown met Mrs. Green. Dr. Smith wrote Fig. 2. The U.S. price is 3.14 dollars. Next sentence."
    raw=core.sentences(text)
    assert raw[0].text=="Mr. Brown met Mrs. Green."
    assert raw[1].text=="Dr. Smith wrote Fig. 2."
    assert raw[2].text=="The U.S. price is 3.14 dollars."
    cooked=prepare_parts(text,raw)
    assert cooked[0].spoken=="Mister Brown met Missus Green."
    assert "3.14" in cooked[2].spoken
    assert all(p.text==text[p.start:p.end] for p in cooked)


def test_decorations_math_and_profiles():
    assert spoken_text("──────")==""
    assert spoken_text("A → B","Natural")=="A , B"
    assert spoken_text("A → B","Study")=="A leads to B"
    assert "minus" in spoken_text("Revenue − Expenses = Profit")
    assert "equals" in spoken_text("Revenue − Expenses = Profit")
    assert spoken_text("# Heading\n**Bold** and [link](https://example.com)",markdown=True)=="Heading Bold and link"
    assert spoken_text("AUCA course",replacements={"AUCA":"A U C A"})=="A U C A course"
    literal=spoken_text("# Title _note_",profile="Literal")
    assert "hash" in literal and "underscore" in literal


def test_margin_omission_is_pdf_only():
    pages=[core.Page(f"Repeated header\nBody page {i} has distinct content.\n{i}") for i in range(1,6)]
    doc=core.Document(Path("test.pdf"),pages,"Book")
    ranges=margin_ranges(doc)
    cooked=prepare_parts(doc.text,core.sentences(doc.text),omitted=ranges)
    assert "Repeated header" not in " ".join(p.spoken for p in cooked)
    assert "distinct content" in " ".join(p.spoken for p in cooked)
    assert margin_ranges(core.Document(Path("note.txt"),pages,"Note"))==[]


def select_all(editor):
    from PySide6.QtGui import QTextCursor
    cursor=editor.textCursor();cursor.select(QTextCursor.SelectionType.Document);editor.setTextCursor(cursor)


def test_rich_html_roundtrip(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    window.new_note();window.convert_rich()
    assert window.note_format=="rich"
    window.editor.insertPlainText("Rich heading")
    select_all(window.editor)
    window.editor.command("heading",2)
    window.editor.command("bold")
    window.editor.command("italic")
    window.editor.command("underline")
    window.editor.command("sub")
    path=tmp_path/"note.html"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(path),""))
    assert window.save()
    assert "<html" in path.read_text(encoding="utf-8")
    document=core.load_document(path)
    window.apply_document(document)
    select_all(window.editor)
    fmt=window.editor.textCursor().charFormat()
    assert fmt.fontItalic() and fmt.fontUnderline()
    assert window.editor.textCursor().blockFormat().headingLevel()==2
    from PySide6.QtGui import QTextCharFormat
    assert fmt.verticalAlignment()==QTextCharFormat.VerticalAlignment.AlignSubScript
    assert not window.editor.document().isModified()


def test_rich_lossy_export_preserves_unsaved_note(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog,QMessageBox
    window.new_note();window.convert_rich();window.editor.insertPlainText("Do not discard this rich note")
    path=tmp_path/"export.txt"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(path),""))
    monkeypatch.setattr(QMessageBox,"question",lambda *a,**k:QMessageBox.StandardButton.Yes)
    assert window.save(True) is False
    assert path.read_text(encoding="utf-8")==window.editor.toPlainText()
    assert window.editor.document().isModified()
    assert window.document.path is None


def test_cancel_conversion_writes_nothing(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog,QMessageBox
    window.new_note();window.convert_rich();window.editor.insertPlainText("Preserve me")
    path=tmp_path/"cancelled.md"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(path),""))
    monkeypatch.setattr(QMessageBox,"question",lambda *a,**k:QMessageBox.StandardButton.Cancel)
    assert not window.save(True)
    assert not path.exists()


def test_markdown_toolbar_edits_source_and_rich_conversion(window):
    window.new_markdown();window.editor.insertPlainText("Heading")
    window.editor.command("heading",2)
    assert window.editor.toPlainText()=="## Heading"
    select_all(window.editor)
    window.editor.command("bold")
    assert window.editor.toPlainText()=="**## Heading**"
    window.convert_rich()
    assert window.note_format=="rich"
    assert window.document.path is None


def test_default_markdown_split_outline_and_save(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    window.new_note()
    assert window.note_format=="markdown"
    text="# First heading\n\nA **bold** sentence.\n\n## Second heading\n"
    window.editor.setPlainText(text)
    window.markdown_view.setCurrentText("Split")
    window.refresh_markdown_workspace()
    assert not window.split_preview.isHidden()
    assert "A bold sentence." in window.split_preview.toPlainText()
    assert window.outline.count()==2
    window.navigate_item(window.outline.item(1))
    assert core.python_position(text,window.editor.textCursor().position())==text.index("## Second")
    path=tmp_path/"markdown.md"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(path),""))
    assert window.save()
    window.apply_document(core.load_document(path))
    assert window.editor.toPlainText()==text
    assert window.note_format=="markdown"


def test_markdown_insertions_are_editable_source(window):
    window.new_note()
    for kind,expected in [("task","- [ ] "),("quote","> "),("link","https://example.com"),
                          ("codeblock","```"),("table","| --- |")]:
        window.editor.clear()
        window.editor.command(kind)
        assert expected in window.editor.toPlainText()


def test_markdown_html_export_renders_formatting(window,tmp_path,monkeypatch):
    from PySide6.QtWidgets import QFileDialog
    window.new_note();window.editor.insertPlainText("# Heading\n\n**Bold** text.")
    path=tmp_path/"rendered.html"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(path),""))
    assert window.save()
    assert window.note_format=="rich"
    assert window.editor.toPlainText()=="Heading\nBold text."
    window.apply_document(core.load_document(path))
    assert "**Bold**" not in window.editor.toPlainText()


def test_recovery_restores_unsaved_source_and_save_cleans_it(window,tmp_path,monkeypatch):
    import studio
    from PySide6.QtWidgets import QFileDialog,QInputDialog
    window.new_note()
    text="# Recovered\n\nUnsaved **draft**."
    window.editor.insertPlainText(text)
    window.write_recovery()
    recovery=window._recovery_path
    assert recovery.is_file()
    # Simulate a restarted reader with an unmodified welcome document.
    window.editor.document().setModified(False)
    window.apply_document(core.Document(None,[core.Page("Welcome")],"Welcome"))
    monkeypatch.setattr(QInputDialog,"getItem",lambda *args,**kwargs:(args[3][0],True))
    window.recover_draft()
    assert window.note_format=="markdown"
    assert window.editor.toPlainText()==text
    assert window.editor.document().isModified()
    path=tmp_path/"recovered.md"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *args,**kwargs:(str(path),""))
    assert window.save()
    assert path.read_text(encoding="utf-8")==text
    assert not recovery.exists()


def test_recovery_discard_cancel_and_focus_modes(window,monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    window.new_note();window.editor.insertPlainText("Keep unless discarded")
    window.write_recovery();path=window._recovery_path
    monkeypatch.setattr(QMessageBox,"question",lambda *a,**k:QMessageBox.StandardButton.Cancel)
    assert not window.confirm_unsaved()
    assert path.exists()
    window.focus_button.click()
    assert window.format_bar.isHidden()
    assert window.splitter.widget(0).isHidden()
    window.focus_button.click()
    assert not window.format_bar.isHidden()
    assert window.format_bar.font.isHidden()
    window.convert_rich()
    assert not window.format_bar.font.isHidden()
    monkeypatch.setattr(QMessageBox,"question",lambda *a,**k:QMessageBox.StandardButton.Discard)
    assert window.confirm_unsaved()
    assert not path.exists()


def test_rich_structure_creates_study_pauses(window):
    from PySide6.QtGui import QTextCursor
    window.new_note();window.convert_rich();window.editor.insertPlainText("Heading\nBody paragraph.\nList item")
    cursor=window.editor.textCursor();cursor.movePosition(QTextCursor.MoveOperation.Start);window.editor.setTextCursor(cursor)
    window.editor.command("heading",1)
    window.profile="Study"
    parts=window.prepare_speech(core.sentences(window.editor.toPlainText()))
    assert parts[0].text=="Heading"
    assert parts[0].pause_after>=.5
    assert parts[1].text=="Body paragraph."


def test_client_frame_and_eight_themes(window,application):
    from PySide6.QtCore import Qt
    from appearance import PALETTES
    assert window.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert len(window.resize_edges)==8
    for name in PALETTES:
        for mode in ("Light","Dark"):
            window.theme_box.setCurrentText(name);window.appearance_mode.setCurrentText(mode)
            application.processEvents()
            assert window.theme_tokens["text"] != window.theme_tokens["bg"]
            assert not window.grab().isNull()
    window.title_bar.maximize();application.processEvents()
    assert window.isMaximized()
    window.title_bar.maximize();application.processEvents()
    assert not window.isMaximized()


def test_native_frame_hit_regions():
    from window_frame import hit_test
    assert [hit_test(x,y,1000,800,6) for x,y in [(0,0),(999,0),(0,799),(999,799)]]==[13,14,16,17]
    assert hit_test(500,400,1000,800,6) is None
    assert hit_test(0,0,1000,800,6,True) is None


def test_gallery_does_not_require_private_design_board(window,monkeypatch):
    from PySide6.QtWidgets import QDialog,QTextBrowser
    from PySide6.QtGui import QTextDocument
    from PySide6.QtCore import QUrl
    seen=[]
    def inspect(dialog):
        browser=dialog.findChild(QTextBrowser)
        seen.append(browser.toPlainText())
        assert not browser.document().resource(QTextDocument.ResourceType.ImageResource,QUrl('book-wave')).isNull()
        return 0
    monkeypatch.setattr(QDialog,'exec',inspect)
    window.design_gallery()
    assert 'Book & wave' in seen[0] and 'Lavender' in seen[0]


def test_plain_document_visible_after_markdown_split(window,application):
    window.new_note();window.markdown_view.setCurrentText("Split")
    window.apply_document(core.Document(None,[core.Page("Visible welcome text")],"Welcome"))
    application.processEvents()
    assert not window.editor.isHidden()
    assert window.editor.width()>100
    assert window.editor.toPlainText()=="Visible welcome text"


def test_standard_frame_fallback(tmp_path,monkeypatch,application):
    import studio
    from PySide6.QtCore import Qt
    monkeypatch.setattr(core,"DATA",tmp_path)
    monkeypatch.setattr(studio,"DATA",tmp_path)
    core.atomic_json(tmp_path/"settings.json",{"standard_frame":True})
    from app import Reader
    w=Reader(register_hotkey=False)
    w.show();application.processEvents()
    assert not w.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert w.title_bar.isHidden()
    assert all(edge.isHidden() for edge in w.resize_edges)
    w.editor.document().setModified(False);w.close()


def test_client_resize_corner_respects_minimum(window,application):
    from PySide6.QtCore import Qt,QPointF,QEvent
    from PySide6.QtGui import QMouseEvent
    edge=window.resize_edges[-1]
    before=window.size()
    start=QPointF(900,700)
    edge.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress,QPointF(2,2),start,Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
    edge.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove,QPointF(42,32),start+QPointF(40,30),Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
    assert window.width()==before.width()+40 and window.height()==before.height()+30
    edge.mouseReleaseEvent(QMouseEvent(QEvent.Type.MouseButtonRelease,QPointF(42,32),start+QPointF(40,30),Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier))
    assert edge.drag_origin is None


def test_client_title_drag_moves_window(window,application):
    from PySide6.QtCore import Qt,QPointF,QEvent
    from PySide6.QtGui import QMouseEvent
    label=window.title_bar.caption
    before=window.pos()
    start=QPointF(before.x()+200,before.y()+20)
    label.mousePressEvent(QMouseEvent(QEvent.Type.MouseButtonPress,QPointF(150,20),start,Qt.MouseButton.LeftButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
    label.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove,QPointF(200,50),start+QPointF(50,30),Qt.MouseButton.NoButton,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier))
    assert window.x()==before.x()+50 and window.y()==before.y()+30
    label.mouseReleaseEvent(QMouseEvent(QEvent.Type.MouseButtonRelease,QPointF(200,50),start+QPointF(50,30),Qt.MouseButton.LeftButton,Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier))


def test_pdf_first_page_scope_and_highlight(window,tmp_path,application,monkeypatch):
    import pymupdf as fitz
    path=tmp_path/"pages.pdf"
    with fitz.open() as pdf:
        pdf.new_page().insert_text((50,80),"First sentence on page one. Another sentence follows.")
        pdf.new_page().insert_text((50,80),"Second page has a distinct sentence, ready to read.")
        pdf.save(path)
    window.apply_document(core.load_document(path,"off"))
    application.processEvents()
    assert window.preview_scroll.isVisible()
    assert not window.tabs.isVisible()
    window.view_mode.setCurrentText("Split");application.processEvents()
    assert window.tabs.isVisible()
    window.goto_page(2)
    captured=[]
    monkeypatch.setattr(window.speech,"start",lambda *a:captured.append(a))
    window.read_page()
    assert "Second page" in captured[0][0][0].text
    window.highlight(0)
    assert window.overlay_rects
    window.zoom_box.setCurrentText("150%")
    assert window.preview_label.pixmap().width()>600


@pytest.mark.parametrize('rotation',[0,90])
def test_direct_pdf_selection_zoom_copy_and_read(window,tmp_path,application,monkeypatch,rotation):
    import pymupdf as fitz
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication
    path=tmp_path/'selection.pdf'
    with fitz.open() as pdf:
        page=pdf.new_page()
        page.insert_text((50,80),'First selected sentence. More words follow.')
        page.set_rotation(rotation)
        pdf.save(path)
    window.apply_document(core.load_document(path,'off'));application.processEvents()
    for zoom in ('75%','150%'):
        window.zoom_box.setCurrentText(zoom);window.render_page();application.processEvents()
        regions=window.pdf_page_regions()
        first=regions[0];last=regions[2]
        scale=window.preview_label.pixmap().width()/window.pdf[0].rect.width
        offset=max(0,(window.preview_label.width()-window.preview_label.pixmap().width())/2)
        def point(region):
            x0,y0,x1,y1=region[2]
            return QPoint(round((x0+x1)/2*scale+offset),round((y0+y1)/2*scale))
        window.select_pdf_points(point(first),point(last))
        assert window.editor.textCursor().selectedText()=='First selected sentence.'
        window.preview_label.copyRequested.emit()
        assert QApplication.clipboard().text()=='First selected sentence.'
    captured=[]
    monkeypatch.setattr(window,'start_speech',lambda *a:captured.append(window.parts))
    window.preview_label.readRequested.emit()
    assert captured[-1][0].text=='First selected sentence.'
    window.preview_label.fromHereRequested.emit()
    assert captured[-1][0].text.startswith('First selected sentence')


def test_two_column_pdf_speech_and_highlights_share_order(window,tmp_path,application):
    import pymupdf
    import re
    path=tmp_path/'columns.pdf'
    def prose(label):
        return (f'{label} begins this original sample paragraph.\n'
                'Students read each column from top to bottom.\n'
                'The next column follows after this paragraph ends.')
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        page.insert_text((325,90),prose('RIGHT'),fontsize=9)
        page.insert_text((40,90),prose('LEFT'),fontsize=9)
        pdf.save(path)
    document=core.load_document(path,'off')
    assert document.pages[0].method=='Text · two columns'
    assert document.text.index('LEFT') < document.text.index('RIGHT')
    window.apply_document(document);application.processEvents()
    regions=window.pdf_page_regions()
    assert len(regions)==len(re.findall(r'\w+',document.text))
    right=document.text.index('RIGHT')
    left_rects=window.sentence_rectangles(core.Sentence(0,right,document.text[:right]))
    right_rects=window.sentence_rectangles(core.Sentence(right,len(document.text),document.text[right:]))
    assert left_rects and right_rects
    assert all(r[2]<300 for r in left_rects)
    assert all(r[0]>300 for r in right_rects)


def test_packaged_window_check_isolates_state_and_renders_markdown(tmp_path,application,monkeypatch):
    import app as reader_module
    import studio
    from frozen_diagnostics import check_reader_window
    private=tmp_path/'normal-user-state'
    for module in (core,studio,reader_module):monkeypatch.setattr(module,'DATA',private)
    result=check_reader_window(application,tmp_path/'diagnostic-state')
    assert all(result.values())
    assert not private.exists()
    assert core.DATA==studio.DATA==reader_module.DATA==private


def test_cross_page_selection_retains_source_range(window,tmp_path,application):
    import pymupdf as fitz
    from PySide6.QtCore import QPoint
    path=tmp_path/'cross-page.pdf'
    with fitz.open() as pdf:
        pdf.new_page().insert_text((50,80),'Page one begins.\nSecond line continues.')
        pdf.new_page().insert_text((50,80),'Page two ends here.')
        pdf.save(path)
    window.apply_document(core.load_document(path,'off'));application.processEvents()
    def choose(index):
        regions=window.pdf_page_regions();r=regions[index]
        scale=window.preview_label.pixmap().width()/window.pdf[window.page_number.value()-1].rect.width
        offset=max(0,(window.preview_label.width()-window.preview_label.pixmap().width())/2)
        x0,y0,x1,y1=r[2]
        p=QPoint(round((x0+x1)/2*scale+offset),round((y0+y1)/2*scale))
        window.select_pdf_points(p,p)
    choose(0)
    window.goto_page(2);application.processEvents()
    window.preview_label.extend_selection=True
    choose(-1)
    selected=window.editor.textCursor().selectedText().replace('\u2029','\n')
    assert 'Page one begins.' in selected
    assert 'Second line continues.' in selected
    assert selected.endswith('Page two ends here.')
    assert window.pdf_selection_range==(0,len(window.document.text.rstrip()))
    window.goto_page(1)
    assert window.editor.textCursor().selectedText().replace('\u2029','\n')==selected


def test_legacy_ocr_cache_rebuilds_coordinates(tmp_path,monkeypatch):
    import pymupdf as fitz
    monkeypatch.setattr(core,'DATA',tmp_path/'state')
    path=tmp_path/'legacy.pdf'
    with fitz.open() as pdf:
        pdf.new_page();pdf.save(path)
    cache=core.DATA/'ocr'/core.pdf_key(path)/'0.json'
    core.atomic_json(cache,{'text':'Old recognized line'})
    class FakeOCR:
        calls=0
        def recognize(self,pix):
            self.calls+=1
            self.boxes=[([[10,10],[100,10],[100,40],[10,40]],'New recognized line')]
            return 'New recognized line'
    ocr=FakeOCR()
    core.load_document(path,'off',ocr=ocr)
    assert ocr.calls==0
    document=core.load_document(path,'auto',ocr=ocr)
    assert ocr.calls==1
    assert document.pages[0].regions
    assert document.pages[0].text=='New recognized line'
    core.load_document(path,'auto',ocr=ocr)
    assert ocr.calls==1


def test_scanned_overlay_uses_retained_regions(window,tmp_path,application):
    import pymupdf as fitz
    path=tmp_path/"scanned.pdf"
    with fitz.open() as pdf:
        pdf.new_page();pdf.save(path)
    page=core.Page("Recognized text.","OCR",[{"start":0,"end":16,"rect":[30,40,200,70]}])
    window.apply_document(core.Document(path,[page],"Scan"))
    assert window.sentence_rectangles(core.Sentence(0,16,page.text))==[[30,40,200,70]]


def test_readonly_text_export_keeps_pdf_source(window,tmp_path,monkeypatch):
    import pymupdf as fitz
    from PySide6.QtWidgets import QFileDialog
    path=tmp_path/"source.pdf"
    with fitz.open() as pdf:
        pdf.new_page().insert_text((50,80),"Original PDF remains unchanged when exporting its reading text.")
        pdf.save(path)
    window.apply_document(core.load_document(path,"off"))
    out=tmp_path/"copy.txt"
    monkeypatch.setattr(QFileDialog,"getSaveFileName",lambda *a,**k:(str(out),""))
    assert window.save(True)
    assert window.document.path==path and window.pdf is not None
    assert out.exists()


@pytest.mark.parametrize('size', [(1024, 720), (800, 600)])
def test_small_window_keeps_playback_controls_inside(window, application, size):
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QWidget
    window.splitter.widget(0).hide()
    window.resize(*size)
    application.processEvents()
    assert window.width() <= size[0]
    assert window.height() <= size[1]
    for widget in (window.play_button, window.voice_combo, window.speed, window.volume):
        origin = widget.mapTo(window, QPoint(0, 0))
        assert origin.x() >= 0 and origin.y() >= 0
        assert origin.x()+widget.width() <= window.width()
        assert origin.y()+widget.height() <= window.height()
    # Every visible command remains reachable after toolbar wrapping.
    for widget in (window.workspace, window.theme_box, window.appearance_mode, window.focus_button):
        origin = widget.mapTo(window, QPoint(0, 0))
        assert origin.x()+widget.width() <= window.width()
        assert origin.y()+widget.height() <= window.height()


@pytest.mark.parametrize("size", [(1024, 720), (800, 600)])
def test_small_markdown_window_reserves_editor_viewport(window, application, size):
    window.new_markdown()
    window.splitter.widget(0).hide()
    window.resize(*size)
    application.processEvents()
    assert window.width() <= size[0] and window.height() <= size[1]
    assert window.editor.viewport().height() >= 100
    assert window.editor.viewport().width() >= 300
    window.focus_button.setChecked(True)
    window.toggle_writing_focus()
    application.processEvents()
    assert window.editor.viewport().height() >= 160


@pytest.mark.parametrize("size", [(1024, 720), (800, 600)])
def test_small_sidebar_keeps_document_lists_usable(window, application, size):
    window.resize(*size)
    window.splitter.widget(0).show()
    application.processEvents()
    assert window.width() <= size[0] and window.height() <= size[1]
    assert window.recent.viewport().height() >= 100
    scroll = window.sidebar_scroll.verticalScrollBar()
    assert scroll.maximum() > 0
    scroll.setValue(scroll.maximum())
    application.processEvents()
    # Scrolling exposes lower actions rather than compressing the lists.
    from PySide6.QtCore import QPoint
    last = window.sidebar_scroll.widget().layout().itemAt(6).widget()
    bottom = last.mapTo(window.sidebar_scroll.viewport(), QPoint(0, last.height()))
    assert bottom.y() <= window.sidebar_scroll.viewport().height()
