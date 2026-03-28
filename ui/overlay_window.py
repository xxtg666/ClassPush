import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer

from ui.message_card import MessageCard
from animations.entrance_animation import EntranceAnimation
from animations.exit_animation import ExitAnimation
from core.signals import get_signals

logger = logging.getLogger("classpush.overlay")


class OverlayWindow(QWidget):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self.signals = get_signals()
        self.dark_mode = config.get("display", {}).get("dark_mode", False)
        self.auto_close_sec = config.get("display", {}).get("auto_close_seconds", 8)
        self.font_size = config.get("display", {}).get("font_size", 28)
        self._current_card = None
        self._entrance_anim = None
        self._exit_anim = None
        self._message_queue = []

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        screen = self.screen()
        if screen:
            geo = screen.geometry()
            self._screen_w = geo.width()
            self._screen_h = geo.height()
            self.setGeometry(geo)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._overlay = QWidget(self)
        self._overlay.setStyleSheet("background: rgba(0,0,0,0.45);")
        self._overlay.setGeometry(self.rect())
        self._overlay.setWindowOpacity(0.0)

    def show_message(self, msg_data: dict):
        if self._current_card:
            self._message_queue.append(msg_data)
            return

        self._display_message(msg_data)

    def _display_message(self, msg_data: dict):
        self._overlay.setGeometry(self.rect())
        self._overlay.show()

        self._current_card = MessageCard(msg_data, self.font_size, self.dark_mode, self)
        self._current_card.dismissed.connect(self._on_dismissed)
        self._current_card.adjustSize()

        card_w = self._current_card.width()
        card_h = self._current_card.height()
        center_x = (self._screen_w - card_w) // 2
        center_y = (self._screen_h - card_h) // 2
        self._current_card.move(center_x, self._screen_h + 100)
        self._current_card.show()
        self._current_card.setWindowOpacity(0.0)

        self._entrance_anim = EntranceAnimation(
            self._current_card, self._overlay, self._screen_w, self._screen_h
        )
        self._entrance_anim.finished.connect(self._on_entrance_done)
        self._entrance_anim.start()

        self.showFullScreen()

    def _on_entrance_done(self):
        if self._current_card:
            self._current_card.setWindowOpacity(1.0)
            self._current_card.start_countdown(self.auto_close_sec, callback=None)

    def _on_dismissed(self):
        if not self._current_card:
            return

        self._current_card.stop_countdown()
        self._exit_anim = ExitAnimation(
            self._current_card, self._overlay, self._screen_w, self._screen_h
        )
        self._exit_anim.finished.connect(self._on_exit_done)
        self._exit_anim.start()

    def _on_exit_done(self):
        if self._current_card:
            self._current_card.deleteLater()
            self._current_card = None

        self._overlay.hide()
        self.hide()

        if self._message_queue:
            next_msg = self._message_queue.pop(0)
            QTimer.singleShot(500, lambda: self._display_message(next_msg))

    def update_config(self, config: dict):
        self.config = config
        self.dark_mode = config.get("display", {}).get("dark_mode", False)
        self.auto_close_sec = config.get("display", {}).get("auto_close_seconds", 8)
        self.font_size = config.get("display", {}).get("font_size", 28)

    def mousePressEvent(self, event):
        if self._current_card and not self._current_card.geometry().contains(
            event.pos()
        ):
            self._on_dismissed()
