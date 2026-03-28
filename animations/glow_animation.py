from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen
import math


class GlowWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._glow = 0.3
        self._anim = None

    def get_glow(self) -> float:
        return self._glow

    def set_glow(self, val: float):
        self._glow = val
        self.update()

    glow = pyqtProperty(float, get_glow, set_glow)

    def start_breathing(self):
        self._anim = QPropertyAnimation(self, b"glow")
        self._anim.setDuration(1000)
        self._anim.setStartValue(0.3)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.SineCurve)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def stop_breathing(self):
        if self._anim:
            self._anim.stop()
            self._anim = None
        self._glow = 0.3
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        alpha = int(self._glow * 255)
        r = int(180 * self._glow + 75 * (1 - self._glow))
        g = int(50 * self._glow + 100 * (1 - self._glow))
        b = int(50 * self._glow + 100 * (1 - self._glow))
        color = QColor(r, g, b, alpha)
        pen = QPen(color, 3)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))
        margin = 2
        painter.drawRoundedRect(
            margin,
            margin,
            self.width() - 2 * margin,
            self.height() - 2 * margin,
            20,
            20,
        )
        painter.end()
