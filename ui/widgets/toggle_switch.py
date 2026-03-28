from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor


class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_pos = 2.0
        self.setFixedSize(52, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"circle_pos")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def get_circle_pos(self) -> float:
        return self._circle_pos

    def set_circle_pos(self, val: float):
        self._circle_pos = val
        self.update()

    circle_pos = pyqtProperty(float, get_circle_pos, set_circle_pos)

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool):
        self._checked = checked
        self._anim.stop()
        if checked:
            self._anim.setStartValue(self._circle_pos)
            self._anim.setEndValue(float(self.width() - 26))
        else:
            self._anim.setStartValue(self._circle_pos)
            self._anim.setEndValue(2.0)
        self._anim.start()

    def toggle(self):
        self.set_checked(not self._checked)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._checked:
            painter.setBrush(QColor(67, 97, 238))
        else:
            painter.setBrush(QColor(200, 200, 200))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 14, 14)

        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(int(self._circle_pos), 2, 24, 24)
        painter.end()
