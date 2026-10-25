"""Theme tokens, scalable vector identity, and client-side move/resize controls."""
from pathlib import Path
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

ASSETS = Path(__file__).parent / "assets"
PALETTES = {
    "Baby blue": ("#4f769b", "#e9f2fa", "#f5f8fc", "#182432", "#24384c", "#a4c9ec"),
    "Coral": ("#a75146", "#fbece7", "#fcf7f3", "#2b2020", "#44302e", "#efb0a1"),
    "Lavender": ("#76608f", "#f0eaf7", "#f9f7fc", "#24202e", "#393046", "#c7b1e4"),
    "Soft brown": ("#806047", "#f1e9df", "#faf7f1", "#28231f", "#3d342d", "#d7b89a"),
}


def tokens(name, dark):
    accent, tint, bg, dark_bg, dark_panel, bright = PALETTES.get(name, PALETTES["Baby blue"])
    return dict(accent=bright if dark else accent, tint=dark_panel if dark else tint,
                bg=dark_bg if dark else bg, panel=dark_panel if dark else "#ffffff",
                text="#f2f0f5" if dark else "#293341", muted="#b3bac5" if dark else "#667384",
                border="#50515d" if dark else "#dce1e9", button=accent)


def logo_svg(accent="#4f769b", concept="book-wave"):
    shapes = {
        "book-wave": '<path d="M32 18C23 11 13 12 6 15v34c9-3 18-2 26 4 8-6 17-7 26-4V15c-7-3-17-4-26 3Z"/><path d="M32 18v35M13 29h5l3-6 4 16 4-10h6l3-8 4 20 4-12h5"/>',
        "page-sound": '<path d="M12 8h26l10 10v38H12ZM38 8v12h10M20 29h12M20 37h10M20 45h13M46 31q9 7 0 14M52 25q16 13 0 26"/>',
        "luma-orbit": '<circle cx="32" cy="32" r="24"/><path d="M20 18v28h25M27 27l5-7 5 22 5-15M12 51l39-39"/>',
    }
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><g fill="none" stroke="{accent}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{shapes[concept]}</g></svg>'


def logo_pixmap(size=64, accent="#4f769b", concept="book-wave"):
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    QSvgRenderer(logo_svg(accent, concept).encode()).render(painter)
    painter.end()
    return pix


class DragLabel(QLabel):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_offset=event.globalPosition().toPoint()-self.window().pos()
            self.dragging=True
        super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if not getattr(self,"dragging",False) or not event.buttons() & Qt.MouseButton.LeftButton:return
        window=self.window()
        if window.isMaximized():
            ratio=event.position().x()/max(1,self.width())
            window.showNormal()
            from PySide6.QtCore import QPoint
            self.drag_offset=QPoint(int(window.width()*ratio),22)
        window.move(event.globalPosition().toPoint()-self.drag_offset)
        event.accept()

    def mouseReleaseEvent(self,event):
        self.dragging=False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging=False
            window = self.window()
            window.showNormal() if window.isMaximized() else window.showMaximized()


class TitleBar(QFrame):
    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("titleBar")
        self.setFixedHeight(46)
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 5, 0)
        self.mark = QLabel()
        self.mark.setPixmap(logo_pixmap(27))
        row.addWidget(self.mark)
        self.caption = DragLabel("Luma Reader")
        self.caption.setObjectName("windowCaption")
        row.addWidget(self.caption, 1)
        for title, glyph, callback in (("Minimize", "−", window.showMinimized),
                    ("Maximize or restore", "□", self.maximize), ("Close", "×", window.close)):
            button = QPushButton(glyph)
            button.setAccessibleName(title)
            button.setToolTip(title)
            button.setFixedSize(42, 34)
            button.setObjectName("windowClose" if title == "Close" else "windowControl")
            button.clicked.connect(callback)
            row.addWidget(button)
            if title=="Maximize or restore":self.max_button=button
        window.windowTitleChanged.connect(self.caption.setText)

    def maximize(self):
        window = self.window()
        window.showNormal() if window.isMaximized() else window.showMaximized()


class ResizeEdge(QWidget):
    def __init__(self, window, edges, cursor):
        super().__init__(window)
        self.edges = edges
        self.drag_origin = None
        self.setCursor(cursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_origin = event.globalPosition().toPoint()
            self.drag_geometry = self.window().geometry()
            event.accept()

    def mouseMoveEvent(self,event):
        if self.drag_origin is None or not event.buttons() & Qt.MouseButton.LeftButton:return
        delta=event.globalPosition().toPoint()-self.drag_origin
        rect=self.drag_geometry
        x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
        window=self.window()
        if self.edges & Qt.Edge.LeftEdge:
            dx=min(delta.x(),w-window.minimumWidth());x+=dx;w-=dx
        if self.edges & Qt.Edge.RightEdge:w=max(window.minimumWidth(),w+delta.x())
        if self.edges & Qt.Edge.TopEdge:
            dy=min(delta.y(),h-window.minimumHeight());y+=dy;h-=dy
        if self.edges & Qt.Edge.BottomEdge:h=max(window.minimumHeight(),h+delta.y())
        window.setGeometry(x,y,w,h)
        event.accept()

    def mouseReleaseEvent(self,event):
        self.drag_origin=None
        event.accept()


def install_frame(window):
    window.custom_frame=not window.state.value.get("standard_frame",False)
    window.setWindowFlag(Qt.WindowType.FramelessWindowHint, window.custom_frame)
    window.setWindowIcon(QIcon(logo_pixmap()))
    # The menu and title bar stay in client space; no native caption is present.
    holder = QWidget()
    from PySide6.QtWidgets import QVBoxLayout
    layout = QVBoxLayout(holder)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    window.title_bar = TitleBar(window)
    menu = window.menuBar()
    layout.addWidget(window.title_bar)
    window.title_bar.setVisible(window.custom_frame)
    layout.addWidget(menu)
    window.setMenuWidget(holder)
    E, C = Qt.Edge, Qt.CursorShape
    specs = [(E.LeftEdge,C.SizeHorCursor),(E.RightEdge,C.SizeHorCursor),(E.TopEdge,C.SizeVerCursor),
             (E.BottomEdge,C.SizeVerCursor),(E.LeftEdge|E.TopEdge,C.SizeFDiagCursor),
             (E.RightEdge|E.TopEdge,C.SizeBDiagCursor),(E.LeftEdge|E.BottomEdge,C.SizeBDiagCursor),
             (E.RightEdge|E.BottomEdge,C.SizeFDiagCursor)]
    window.resize_edges = [ResizeEdge(window, edges, cursor) for edges, cursor in specs]
    if window.custom_frame:
        from window_frame import configure_native
        window.winId()
        configure_native(window)


def place_edges(window):
    w, h, s = window.width(), window.height(), 6
    boxes = [(0,s,s,h-2*s),(w-s,s,s,h-2*s),(s,0,w-2*s,s),(s,h-s,w-2*s,s),
             (0,0,s,s),(w-s,0,s,s),(0,h-s,s,s),(w-s,h-s,s,s)]
    for edge, geometry in zip(getattr(window,"resize_edges",[]), boxes):
        edge.setGeometry(*geometry)
        edge.setVisible(getattr(window,"custom_frame",True) and not window.isMaximized())
        edge.raise_()
