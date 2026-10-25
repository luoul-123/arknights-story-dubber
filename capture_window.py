"""Capture a selected HWND without reading or modifying the target process."""

from PIL import Image, ImageStat
import ctypes
from ctypes import wintypes
import win32gui
import win32ui


_print_window = ctypes.windll.user32.PrintWindow
_print_window.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
_print_window.restype = wintypes.BOOL


def print_window(hwnd: int) -> Image.Image:
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top
    source_dc = win32gui.GetWindowDC(hwnd)
    dc = win32ui.CreateDCFromHandle(source_dc)
    memory_dc = dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    try:
        bitmap.CreateCompatibleBitmap(dc, width, height)
        memory_dc.SelectObject(bitmap)
        if not _print_window(hwnd, memory_dc.GetSafeHdc(), 2):
            raise RuntimeError("PrintWindow returned no image")
        data = bitmap.GetBitmapBits(True)
        image = Image.frombuffer("RGB", (width, height), data, "raw", "BGRX", 0, 1).copy()
        center = image.crop((width // 10, height // 10, width * 9 // 10, height * 9 // 10))
        if ImageStat.Stat(center.convert("L")).stddev[0] < 2:
            raise RuntimeError("PrintWindow returned a blank client area")
        return image
    finally:
        win32gui.DeleteObject(bitmap.GetHandle())
        memory_dc.DeleteDC()
        dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, source_dc)
