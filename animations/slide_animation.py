from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtWidgets import QWidget


class SlideAnimation:
    @staticmethod
    def slide_in(
        widget: QWidget, from_right: bool = True, duration: int = 300
    ) -> QPropertyAnimation:
        parent = widget.parentWidget()
        if parent:
            pw = parent.width()
        else:
            pw = 1920

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        if from_right:
            anim.setStartValue(QPoint(pw, widget.y()))
            anim.setEndValue(QPoint(pw - widget.width() - 16, widget.y()))
        else:
            anim.setStartValue(QPoint(-widget.width(), widget.y()))
            anim.setEndValue(QPoint(16, widget.y()))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        return anim

    @staticmethod
    def slide_out(
        widget: QWidget, to_right: bool = True, duration: int = 300
    ) -> QPropertyAnimation:
        parent = widget.parentWidget()
        if parent:
            pw = parent.width()
        else:
            pw = 1920

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        if to_right:
            anim.setStartValue(widget.pos())
            anim.setEndValue(QPoint(pw, widget.y()))
        else:
            anim.setStartValue(widget.pos())
            anim.setEndValue(QPoint(-widget.width(), widget.y()))
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        return anim
