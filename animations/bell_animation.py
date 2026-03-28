import math
from PyQt6.QtCore import (
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QEasingCurve,
    QTimer,
)
from PyQt6.QtCore import pyqtProperty
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter


class BellWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0.0
        self._icon = "\U0001f514"
        self.setFixedSize(48, 48)

    def get_rotation(self) -> float:
        return self._rotation

    def set_rotation(self, val: float):
        self._rotation = val
        self.update()

    rotation = pyqtProperty(float, get_rotation, set_rotation)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        painter.translate(-self.width() / 2, -self.height() / 2)
        font = painter.font()
        font.setPixelSize(32)
        painter.setFont(font)
        painter.drawText(self.rect(), 0x0004, self._icon)
        painter.end()


class BellShakeAnimation(QSequentialAnimationGroup):
    def __init__(self, bell: BellWidget, parent=None):
        super().__init__(parent)
        for i in range(3):
            shake_right = QPropertyAnimation(bell, b"rotation")
            shake_right.setDuration(80)
            shake_right.setStartValue(0)
            shake_right.setEndValue(15)
            shake_right.setEasingCurve(QEasingCurve.Type.InOutSine)

            shake_left = QPropertyAnimation(bell, b"rotation")
            shake_left.setDuration(160)
            shake_left.setStartValue(15)
            shake_left.setEndValue(-15)
            shake_left.setEasingCurve(QEasingCurve.Type.InOutSine)

            shake_back = QPropertyAnimation(bell, b"rotation")
            shake_back.setDuration(80)
            shake_back.setStartValue(-15)
            shake_back.setEndValue(0)
            shake_back.setEasingCurve(QEasingCurve.Type.InOutSine)

            self.addAnimation(shake_right)
            self.addAnimation(shake_left)
            self.addAnimation(shake_back)
