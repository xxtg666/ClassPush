from PyQt6.QtCore import (
    QPropertyAnimation,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    QEasingCurve,
)
from PyQt6.QtWidgets import QWidget


class StaggerAnimation(QSequentialAnimationGroup):
    def __init__(self, widgets: list, delay_ms: int = 80, parent=None):
        super().__init__(parent)
        for i, widget in enumerate(widgets):
            if i > 0:
                self.addPause(delay_ms)

            parallel = QParallelAnimationGroup()

            x_offset = QPropertyAnimation(widget, b"pos")
            x_offset.setDuration(250)
            start_pos = widget.pos()
            x_offset.setStartValue(start_pos)
            x_offset.setEndValue(start_pos)
            x_offset.setEasingCurve(QEasingCurve.Type.OutCubic)

            fade = QPropertyAnimation(widget, b"windowOpacity")
            fade.setDuration(250)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)

            parallel.addAnimation(fade)
            self.addAnimation(parallel)
