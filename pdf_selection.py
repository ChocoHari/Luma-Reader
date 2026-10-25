"""Page-canvas selection with source-text offsets shared by speech and copy."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QMenu


def nearest_region(regions,x,y):
    if not regions:return None
    def distance(region):
        x0,y0,x1,y1=region[2]
        return max(x0-x,0,x-x1)**2+max(y0-y,0,y-y1)**2
    return min(regions,key=distance)


class PdfCanvas(QLabel):
    selectionMoved=Signal(object,object)
    selectionStarted=Signal()
    copyRequested=Signal()
    readRequested=Signal()
    fromHereRequested=Signal()

    def __init__(self):
        super().__init__('Original page')
        self.anchor=None
        self.extend_selection=False
        self.setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName('PDF page. Drag to select text; right click for reading and copy commands.')

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.setFocus()
            self.extend_selection=bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            self.anchor=event.position().toPoint()
            self.selectionStarted.emit()
            self.selectionMoved.emit(self.anchor,self.anchor)
        else:super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if self.anchor is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.selectionMoved.emit(self.anchor,event.position().toPoint())

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.anchor is not None:
            self.selectionMoved.emit(self.anchor,event.position().toPoint())
            self.anchor=None

    def contextMenuEvent(self,event):
        menu=QMenu(self)
        menu.addAction('Copy selection',self.copyRequested.emit)
        menu.addAction('Read selection',self.readRequested.emit)
        menu.addAction('Read from here',self.fromHereRequested.emit)
        menu.exec(event.globalPos())

    def keyPressEvent(self,event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key()==Qt.Key.Key_C:
            self.copyRequested.emit()
        else:super().keyPressEvent(event)
