from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient


class CountdownProgressBar(QWidget):
    def __init__(self, total_seconds=8, parent=None):
        super().__init__(parent)
        self._total_ms = total_seconds * 1000
        self._elapsed_ms = 0
        self._progress = 1.0
        self.setFixedHeight(4)

        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._finished_callback = None

    def start(self, total_seconds=None):
        if total_seconds is not None:
            self._total_ms = total_seconds * 1000
        self._elapsed_ms = 0
        self._progress = 1.0
        self.update()
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def set_finished_callback(self, callback):
        self._finished_callback = callback

    def _tick(self):
        self._elapsed_ms += 50
        self._progress = max(0.0, 1.0 - self._elapsed_ms / self._total_ms)
        self.update()
        if self._elapsed_ms >= self._total_ms:
            self._timer.stop()
            if self._finished_callback:
                self._finished_callback()

    def get_progress(self) -> float:
        return self._progress

    def set_progress(self, val: float):
        self._progress = val
        self.update()

    progress = pyqtProperty(float, get_progress, set_progress)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor(200, 200, 200, 60))
        painter.drawRoundedRect(self.rect(), 2, 2)

        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(102, 126, 234))
        grad.setColorAt(1, QColor(118, 75, 162))
        painter.setBrush(grad)

        w = int(self.width() * self._progress)
        if w > 0:
            painter.drawRoundedRect(0, 0, w, self.height(), 2, 2)

        painter.end()
