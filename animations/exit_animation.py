from PyQt6.QtCore import (
    QPropertyAnimation,
    QParallelAnimationGroup,
    QEasingCurve,
    QPoint,
)
from PyQt6.QtWidgets import QWidget


class ExitAnimation(QParallelAnimationGroup):
    def __init__(
        self, card: QWidget, overlay: QWidget, screen_w: int, screen_h: int, parent=None
    ):
        super().__init__(parent)

        card_w = card.width()
        card_h = card.height()
        center_x = (screen_w - card_w) // 2
        center_y = (screen_h - card_h) // 2

        card_move = QPropertyAnimation(card, b"pos")
        card_move.setDuration(300)
        card_move.setStartValue(QPoint(center_x, center_y))
        card_move.setEndValue(QPoint(center_x, -card_h - 50))
        card_move.setEasingCurve(QEasingCurve.Type.InCubic)

        card_fade = QPropertyAnimation(card, b"windowOpacity")
        card_fade.setDuration(300)
        card_fade.setStartValue(1.0)
        card_fade.setEndValue(0.0)

        overlay_fade = QPropertyAnimation(overlay, b"windowOpacity")
        overlay_fade.setDuration(200)
        overlay_fade.setStartValue(0.45)
        overlay_fade.setEndValue(0.0)

        self.addAnimation(card_move)
        self.addAnimation(card_fade)
        self.addAnimation(overlay_fade)
