from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush


class GlassmorphismMixin:
    def apply_glass_effect(
        self, widget: QWidget, opacity: float = 0.92, blur_radius: int = 15
    ):
        widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._glass_opacity = opacity
        self._blur_radius = blur_radius

    def paint_glass_background(
        self,
        widget: QWidget,
        painter: QPainter,
        corner_radius: int = 20,
        dark_mode: bool = False,
    ):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if dark_mode:
            bg = QColor(30, 30, 46, int(255 * self._glass_opacity))
            border = QColor(255, 255, 255, 40)
        else:
            bg = QColor(255, 255, 255, int(255 * self._glass_opacity))
            border = QColor(255, 255, 255, 153)

        painter.setBrush(QBrush(bg))
        pen = painter.pen()
        pen.setColor(border)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRoundedRect(
            widget.rect().adjusted(1, 1, -1, -1), corner_radius, corner_radius
        )


class GlassCard(QWidget, GlassmorphismMixin):
    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self._dark_mode = dark_mode
        self.apply_glass_effect(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.paint_glass_background(
            self, painter, corner_radius=20, dark_mode=self._dark_mode
        )
        painter.end()
