"""Render original Luma demo content and brand assets; never open personal books."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QPainter,QFont,QColor,QPixmap
from PySide6.QtCore import QRectF,Qt
import reader_core as core,studio
from appearance import logo_pixmap,logo_svg
from app import Reader

ROOT=core.ROOT
OUT=ROOT/'marketing/assets'
DEMO='''# A quieter place to read

## Make room for one good idea

Read a little. Listen again. Write what matters in your own words.

Luma brings original pages, local voices and simple notes into one workspace.

## A small study plan

- [x] Open the chapter
- [ ] Listen to one section
- [ ] Summarise the main idea

> A useful note is a conversation with your future self.

**Today's question:** What changed in my understanding?
'''


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    demo_dir=ROOT/'marketing/demo';demo_dir.mkdir(exist_ok=True)
    (demo_dir/'study-notes.md').write_text(DEMO,encoding='utf-8')
    app=QApplication.instance() or QApplication([])
    for font in Path('C:/Windows/Fonts').glob('segoeui*.ttf'):QFontDatabase.addApplicationFont(str(font))
    core.DATA=studio.DATA=Path(tempfile.mkdtemp(prefix='luma-marketing-'))
    w=Reader(register_hotkey=False);w.resize(1440,960);w.show();app.processEvents()
    w.new_note();w.editor.setPlainText(DEMO);w.document.title='Study notes · original demo'
    w.markdown_view.setCurrentText('Split');w.refresh_markdown_workspace()
    index=next((i for i in range(w.voice_combo.count()) if 'cori' in str(w.voice_combo.itemData(i)).lower()),-1)
    if index>=0:w.voice_combo.setCurrentIndex(index)
    for name,mode in [('Baby blue','Light'),('Lavender','Dark'),('Coral','Light'),('Soft brown','Dark')]:
        w.theme_box.setCurrentText(name);w.appearance_mode.setCurrentText(mode)
        w.update_title();app.processEvents();w.grab().save(str(OUT/f'editor-{name.lower().replace(" ","-")}-{mode.lower()}.png'))
    # An original demo page, rendered privately for the screenshot rather than shipping a personal textbook.
    import pymupdf
    page_path=core.DATA/'original-demo.pdf'
    with pymupdf.open() as pdf:
        p=pdf.new_page(width=595,height=700)
        p.draw_rect(pymupdf.Rect(0,0,595,700),color=None,fill=(.97,.98,1))
        p.insert_text((50,80),'A quieter place to read',fontsize=25,color=(.18,.28,.40))
        p.insert_textbox(pymupdf.Rect(50,115,545,260),'Bring your attention back to the page.\n\nA short reading session can begin with one question:\nWhat is the most useful idea here?',fontsize=14,color=(.2,.25,.3))
        p.draw_rect(pymupdf.Rect(50,290,545,440),color=None,fill=(.89,.93,.97))
        p.insert_text((72,328),'READ  >  LISTEN  >  REFLECT',fontsize=18,color=(.22,.36,.5))
        p.insert_textbox(pymupdf.Rect(72,355,520,425),'Keep an original page in view. Listen with a local voice.\nWrite a small note that helps you remember.',fontsize=12)
        p.insert_text((50,615),'Original Luma demonstration content',fontsize=10,color=(.4,.45,.5))
        pdf.save(page_path)
    w.editor.document().setModified(False)
    w.apply_document(core.load_document(page_path,'off'))
    w.document.title='Reading demo · original content'
    w.theme_box.setCurrentText('Baby blue');w.appearance_mode.setCurrentText('Light')
    w.zoom_box.setCurrentText('Fit page');w.update_title();app.processEvents();w.render_page()
    w.grab().save(str(OUT/'pdf-original-page.png'))
    w.editor.document().setModified(False);w.close()
    for color,label in [('#4f769b','blue'),('#c7b1e4','lavender')]:
        (OUT/f'book-wave-{label}.svg').write_text(logo_svg(color),encoding='utf-8')
        logo_pixmap(512,color).save(str(OUT/f'book-wave-{label}.png'))
    for width,height,name in [(1600,900,'hero-1600x900.png'),(1200,630,'social-1200x630.png')]:
        pix=QPixmap(width,height);pix.fill(QColor('#f5f8fc'))
        painter=QPainter(pix);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(65,65,logo_pixmap(110))
        painter.setPen(QColor('#293341'));painter.setFont(QFont('Segoe UI',42,QFont.Weight.Bold));painter.drawText(195,143,'Luma Reader')
        painter.setFont(QFont('Segoe UI',31));painter.drawText(70,260,'A quieter place')
        painter.drawText(70,316,'to read.')
        painter.setPen(QColor('#4f769b'));painter.setFont(QFont('Segoe UI',19))
        for line,text in enumerate(('Original pages.','Local voices.','Your notes.')):painter.drawText(72,385+line*36,text)
        painter.setPen(QColor('#667384'));painter.setFont(QFont('Segoe UI',11));painter.drawText(72,height-50,'WINDOWS  /  DEVELOPMENT PREVIEW')
        screenshot=QPixmap(str(OUT/'editor-baby-blue-light.png')).scaled(int(width*.52),height-210,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(width-screenshot.width()-40,180 if height<700 else 250,screenshot)
        painter.end();pix.save(str(OUT/name))
    print('Rendered five original-content screenshots, two banners and four logo exports.')


if __name__=='__main__':main()
