from PyQt6.QtCore import (
    QPropertyAnimation,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    QEasingCurve,
    QPoint,
    QTimer,
)
from PyQt6.QtCore import pyqtProperty
from PyQt6.QtWidgets import QWidget


class EntranceAnimation(QSequentialAnimationGroup):
    def __init__(
        self, card: QWidget, overlay: QWidget, screen_w: int, screen_h: int, parent=None
    ):
        super().__init__(parent)
        self.card = card
        self.overlay = overlay

        card_w = card.width()
        card_h = card.height()
        center_x = (screen_w - card_w) // 2
        center_y = (screen_h - card_h) // 2

        overlay_fade = QPropertyAnimation(overlay, b"windowOpacity")
        overlay_fade.setDuration(300)
        overlay_fade.setStartValue(0.0)
        overlay_fade.setEndValue(0.45)
        overlay_fade.setEasingCurve(QEasingCurve.Type.InOutQuad)

        card_move = QPropertyAnimation(card, b"pos")
        card_move.setDuration(400)
        card_move.setStartValue(QPoint(center_x, screen_h + 100))
        card_move.setEndValue(QPoint(center_x, center_y))
        card_move.setEasingCurve(QEasingCurve.Type.OutBack)

        card_fade = QPropertyAnimation(card, b"windowOpacity")
        card_fade.setDuration(200)
        card_fade.setStartValue(0.0)
        card_fade.setEndValue(1.0)

        parallel = QParallelAnimationGroup()
        parallel.addAnimation(card_move)
        parallel.addAnimation(card_fade)

        self.addAnimation(overlay_fade)
        self.addAnimation(parallel)
