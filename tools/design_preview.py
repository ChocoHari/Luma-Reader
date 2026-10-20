"""Produce vector logo alternatives and a local eight-theme design board."""
import os
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase,QPainter,QPixmap,QColor,QFont
from PySide6.QtCore import Qt,QRect
from appearance import ASSETS,PALETTES,tokens,logo_svg,logo_pixmap
app=QApplication.instance() or QApplication([])
for name in ("segoeui.ttf","segoeuib.ttf"):
    QFontDatabase.addApplicationFont("C:/Windows/Fonts/"+name)
ASSETS.mkdir(exist_ok=True)
concepts=[("book-wave","Book & wave · recommended"),("page-sound","Page & sound"),("luma-orbit","Luma orbit")]
for name,_ in concepts:
    (ASSETS/(name+".svg")).write_text(logo_svg(concept=name),encoding="utf-8")
logo_pixmap(256).save(str(ASSETS/"luma.png"))
logo_pixmap(256).save(str(ASSETS/"luma.ico"))
pix=QPixmap(1400,1040);pix.fill(QColor("#f4f6fa"))
p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing)
p.setFont(QFont("Segoe UI",26,QFont.Weight.Bold));p.setPen(QColor("#25334a"));p.drawText(45,60,"Luma Reader · a quieter place to read")
p.setFont(QFont("Segoe UI",12));p.drawText(45,95,"CLIENT-SIDE WINDOW FRAME  /  PDF FIRST  /  RICH NOTES  /  LOCAL VOICES")
for i,(name,label) in enumerate(concepts):
    x=45+i*450
    p.fillRect(x,125,420,150,QColor("white"));p.drawPixmap(x+24,148,logo_pixmap(80,concept=name))
    p.setPen(QColor("#25334a"));p.setFont(QFont("Segoe UI",13));p.drawText(x+120,205,label)
html=['<h1>Luma Reader · identity and themes</h1><p>Book & wave is the default. Alternative vector marks are preserved in assets.</p><table cellpadding="14"><tr>']
for name,label in concepts:
    html.append(f'<td><img width="70" height="70" src="{(ASSETS/(name+".svg")).as_uri()}"><br>{label}</td>')
html.append('</tr></table><h2>Four colours · light and dark</h2><table cellpadding="20">')
for row,name in enumerate(PALETTES):
    html.append('<tr>')
    for col,dark in enumerate((False,True)):
        t=tokens(name,dark);x=45+col*675;y=310+row*175
        p.fillRect(x,y,645,150,QColor(t['bg']));p.fillRect(x,y,645,34,QColor(t['panel']))
        p.setPen(QColor(t['text']));p.setFont(QFont("Segoe UI",13,QFont.Weight.Bold));p.drawText(x+15,y+24,f"{name} · {'Dark' if dark else 'Light'}")
        p.setPen(QColor(t['muted']));p.setFont(QFont("Segoe UI",12));p.drawText(x+20,y+73,"Original pages. Comfortable notes. Natural speech.")
        p.fillRect(x+20,y+95,110,34,QColor(t['button']));p.setPen(QColor('white'));p.drawText(x+40,y+118,"Play  ▶")
        p.fillRect(x+148,y+95,470,34,QColor(t['panel']));p.setPen(QColor(t['text']));p.drawText(x+166,y+118,"A considered space for reading and listening")
        html.append(f'<td bgcolor="{t["bg"]}"><font color="{t["text"]}"><b>{name} · {"Dark" if dark else "Light"}</b><p>A considered space for reading and listening</p></font></td>')
    html.append('</tr>')
p.end();html.append('</table>')
(ASSETS/'design-gallery.html').write_text(''.join(html),encoding='utf-8')
out=ASSETS.parent/'verification';out.mkdir(exist_ok=True)
pix.save(str(out/'v2-design-board.png'))
print('Design board, three SVG concepts, and application icon created.')
