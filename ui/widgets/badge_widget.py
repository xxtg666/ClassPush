from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QFont


class BadgeWidget(QWidget):
    def __init__(self, count=0, parent=None):
        super().__init__(parent)
        self._count = count
        self.setFixedSize(24, 24)

    def set_count(self, count: int):
        self._count = count
        self.update()

    def paintEvent(self, event):
        if self._count <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(255, 59, 48))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)
        text = str(min(self._count, 99)) if self._count <= 99 else "99+"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
