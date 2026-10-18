"""Windows non-client integration for Luma's client-side title bar."""
import ctypes
import sys
from ctypes import wintypes
from PySide6.QtCore import QPoint, Qt


def hit_test(x,y,width,height,border,maximized=False):
    if maximized:return None
    left,right=x<border,x>=width-border
    top,bottom=y<border,y>=height-border
    if top:return 13 if left else 14 if right else 12
    if bottom:return 16 if left else 17 if right else 15
    if left:return 10
    if right:return 11
    return None


def configure_native(window):
    if sys.platform!='win32' or window.windowHandle() is None:return
    if window.windowHandle().screen() is None:return
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.platformName()!='windows':return
    user=ctypes.windll.user32
    get=user.GetWindowLongPtrW
    get.argtypes=[wintypes.HWND,ctypes.c_int];get.restype=ctypes.c_ssize_t
    put=user.SetWindowLongPtrW
    put.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_ssize_t];put.restype=ctypes.c_ssize_t
    hwnd=int(window.winId())
    style=get(hwnd,-16)
    put(hwnd,-16,style|0x00040000|0x00020000|0x00010000|0x00080000)
    user.SetWindowPos(wintypes.HWND(hwnd),None,0,0,0,0,0x0027)


def native_event(window,message):
    if sys.platform!='win32' or not getattr(window,'custom_frame',False) or not hasattr(window,'title_bar'):return None
    msg=wintypes.MSG.from_address(int(message))
    if msg.message==0x0083 and msg.wParam: # WM_NCCALCSIZE: retain all client space
        return True,0
    if msg.message==0x0084: # WM_NCHITTEST; LPARAM uses signed physical screen coordinates
        x=ctypes.c_short(msg.lParam & 0xffff).value
        y=ctypes.c_short((msg.lParam>>16)&0xffff).value
        point=wintypes.POINT(x,y)
        ctypes.windll.user32.ScreenToClient.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
        ctypes.windll.user32.ScreenToClient(msg.hWnd,ctypes.byref(point))
        scale=window.devicePixelRatioF()
        point=QPoint(round(point.x/scale),round(point.y/scale))
        edge=hit_test(point.x(),point.y(),window.width(),window.height(),6,window.isMaximized())
        if edge:return True,edge
        bar=window.title_bar
        button=bar.max_button
        if button.rect().contains(button.mapFrom(window,point)):return True,9
        if bar.caption.rect().contains(bar.caption.mapFrom(window,point)):return True,2
    if msg.message in (0x00a1,0x00a2) and msg.wParam==9:
        if msg.message==0x00a1:window.title_bar.max_button.setDown(True)
        else:
            window.title_bar.max_button.setDown(False)
            window.title_bar.maximize()
        return True,0
    if msg.message==0x0024: # WM_GETMINMAXINFO, monitor-relative physical pixels
        class MINMAXINFO(ctypes.Structure):
            _fields_=[(name,wintypes.POINT) for name in ('reserved','maxSize','maxPosition','minTrackSize','maxTrackSize')]
        class MONITORINFO(ctypes.Structure):
            _fields_=[('cbSize',wintypes.DWORD),('monitor',wintypes.RECT),('work',wintypes.RECT),('flags',wintypes.DWORD)]
        user=ctypes.windll.user32
        user.MonitorFromWindow.argtypes=[wintypes.HWND,wintypes.DWORD]
        user.MonitorFromWindow.restype=wintypes.HANDLE
        user.GetMonitorInfoW.argtypes=[wintypes.HANDLE,ctypes.c_void_p]
        monitor=user.MonitorFromWindow(msg.hWnd,2)
        info=MONITORINFO();info.cbSize=ctypes.sizeof(info)
        if user.GetMonitorInfoW(wintypes.HANDLE(monitor),ctypes.byref(info)):
            target=MINMAXINFO.from_address(msg.lParam)
            target.maxPosition=wintypes.POINT(info.work.left-info.monitor.left,info.work.top-info.monitor.top)
            target.maxSize=wintypes.POINT(info.work.right-info.work.left,info.work.bottom-info.work.top)
            ratio=window.devicePixelRatioF()
            target.minTrackSize=wintypes.POINT(round(window.minimumWidth()*ratio),round(window.minimumHeight()*ratio))
            return True,0
    return None
