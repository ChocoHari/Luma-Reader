"""Create a silent captioned tour from original-content UI screenshots."""
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
import cv2
import numpy as np
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap,QPainter,QColor,QFont,QImage,QFontDatabase
from PySide6.QtCore import Qt,QRect

ROOT=Path(__file__).resolve().parents[1]
SCENES=[('pdf-original-page.png','Keep original pages in view.'),
        ('editor-baby-blue-light.png','Write Markdown beside a live preview.'),
        ('editor-lavender-dark.png','Choose a light or dark workspace.'),
        ('editor-coral-light.png','Keep notes and local reading together.'),
        ('editor-soft-brown-dark.png','Luma Reader — development preview.')]


def main():
    app=QApplication.instance() or QApplication([])
    for file in Path('C:/Windows/Fonts').glob('segoeui*.ttf'):QFontDatabase.addApplicationFont(str(file))
    assets=ROOT/'marketing/assets'
    target=assets/'luma-captioned-tour.mp4'
    writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'mp4v'),10,(1280,720))
    if not writer.isOpened():raise RuntimeError('MP4 encoder unavailable')
    captions=[]
    try:
        for index,(file,caption) in enumerate(SCENES):
            source=QPixmap(str(assets/file))
            if source.isNull():raise ValueError(f'Missing screenshot: {file}')
            image=QPixmap(1280,720);image.fill(QColor('#17202c'))
            painter=QPainter(image)
            painter.setPen(QColor('#d7e5f3'));painter.setFont(QFont('Segoe UI',20,QFont.Weight.Bold))
            painter.drawText(QRect(35,15,1210,50),Qt.AlignmentFlag.AlignCenter,'Luma Reader · screenshot tour')
            scaled=source.scaled(1200,520,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap((1280-scaled.width())//2,85,scaled)
            painter.setPen(QColor('white'));painter.setFont(QFont('Segoe UI',22))
            painter.drawText(QRect(30,620,1220,50),Qt.AlignmentFlag.AlignCenter,caption)
            painter.setFont(QFont('Segoe UI',10));painter.setPen(QColor('#b4c1cf'))
            painter.drawText(QRect(30,676,1220,25),Qt.AlignmentFlag.AlignCenter,'DEVELOPMENT PREVIEW · ORIGINAL DEMO CONTENT · SILENT TOUR')
            painter.end()
            rgb=image.toImage().convertToFormat(QImage.Format.Format_RGB888)
            array=np.frombuffer(rgb.bits(),dtype=np.uint8).reshape(720,rgb.bytesPerLine())[:,:1280*3].reshape(720,1280,3)
            frame=cv2.cvtColor(array,cv2.COLOR_RGB2BGR)
            for _ in range(40):writer.write(frame)
            start=index*4;end=start+4
            captions.append(f'{index+1}\n00:00:{start:02d},000 --> 00:00:{end:02d},000\n{caption}\n')
    finally:writer.release()
    (ROOT/'marketing/demo-captions.srt').write_text('\n'.join(captions),encoding='utf-8')
    capture=cv2.VideoCapture(str(target))
    frames=int(capture.get(cv2.CAP_PROP_FRAME_COUNT));fps=capture.get(cv2.CAP_PROP_FPS)
    ok,frame=capture.read();capture.release()
    if not ok or frames!=200 or fps!=10:raise RuntimeError('Encoded tour failed verification')
    cv2.imwrite(str(ROOT/'verification/marketing-video-first-frame.png'),frame)
    print(f'Verified silent MP4: {frames} frames at {fps:g} fps, 1280×720, 20 seconds.')


if __name__=='__main__':main()
