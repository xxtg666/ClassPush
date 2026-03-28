from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient


class AnimatedButton(QPushButton):
    def __init__(
        self, text="", parent=None, gradient_start="#667eea", gradient_end="#764ba2"
    ):
        super().__init__(text, parent)
        self._hover_brightness = 1.0
        self._press_scale = 1.0
        self._gradient_start = gradient_start
        self._gradient_end = gradient_end
        self.setCursor(QPushButton().cursor())
        self.setFixedHeight(52)
        self.setMinimumWidth(180)
        self.setStyleSheet(self._build_style())

    def _build_style(self):
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, stop:0 {self._gradient_start}, stop:1 {self._gradient_end});
                color: white;
                border: none;
                border-radius: 26px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 32px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, stop:0 {self._lighten(self._gradient_start)}, stop:1 {self._lighten(self._gradient_end)});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, stop:0 {self._darken(self._gradient_start)}, stop:1 {self._darken(self._gradient_end)});
            }}
        """

    def set_gradient(self, start: str, end: str):
        self._gradient_start = start
        self._gradient_end = end
        self.setStyleSheet(self._build_style())

    @staticmethod
    def _lighten(hex_color: str, amount: int = 30) -> str:
        c = QColor(hex_color)
        r = min(255, c.red() + amount)
        g = min(255, c.green() + amount)
        b = min(255, c.blue() + amount)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def _darken(hex_color: str, amount: int = 30) -> str:
        c = QColor(hex_color)
        r = max(0, c.red() - amount)
        g = max(0, c.green() - amount)
        b = max(0, c.blue() - amount)
        return f"#{r:02x}{g:02x}{b:02x}"
