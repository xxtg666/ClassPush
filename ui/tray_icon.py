import logging
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import pyqtSignal, Qt

logger = logging.getLogger("classpush.tray")


class TrayIcon(QSystemTrayIcon):
    show_panel_requested = pyqtSignal()
    toggle_sidebar_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    mute_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._unread_count = 0
        self._is_muted = False
        self._setup_icon()
        self._setup_menu()
        self.activated.connect(self._on_activated)

    def _setup_icon(self):
        pixmap = self._create_icon(0)
        self.setIcon(QIcon(pixmap))
        self.setToolTip("ClassPush \u73ed\u63a8")

    def _create_icon(self, count: int) -> QPixmap:
        size = 64
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(67, 97, 238))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, size - 8, size - 8)

        font = QFont()
        font.setPixelSize(28)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "\U0001f514")

        if count > 0:
            badge_size = 24
            painter.setBrush(QColor(255, 59, 48))
            painter.drawEllipse(size - badge_size - 2, 2, badge_size, badge_size)

            font.setPixelSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            text = str(min(count, 99)) if count <= 99 else "99+"
            painter.drawText(
                size - badge_size - 2,
                2,
                badge_size,
                badge_size,
                Qt.AlignmentFlag.AlignCenter,
                text,
            )

        painter.end()
        return pixmap

    def _setup_menu(self):
        self._menu = QMenu()

        self._show_action = self._menu.addAction(
            "\U0001f4cb \u663e\u793a\u6d88\u606f\u9762\u677f"
        )
        self._show_action.triggered.connect(self.toggle_sidebar_requested.emit)

        self._console_action = self._menu.addAction(
            "\U0001f4dd \u6253\u5f00\u63a7\u5236\u53f0"
        )
        self._console_action.triggered.connect(self.show_panel_requested.emit)

        self._menu.addSeparator()

        self.mute_action = self._menu.addAction("\U0001f507 \u9759\u97f3\u6a21\u5f0f")
        self.mute_action.setCheckable(True)
        self.mute_action.triggered.connect(self._toggle_mute)

        self._menu.addSeparator()

        self._quit_action = self._menu.addAction("\u274c \u9000\u51fa")
        self._quit_action.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(self._menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_panel_requested.emit()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_sidebar_requested.emit()

    def _toggle_mute(self, checked):
        self._is_muted = checked
        self.mute_toggled.emit(self._is_muted)
        if self._is_muted:
            self.mute_action.setText("\U0001f50a \u53d6\u6d88\u9759\u97f3")
        else:
            self.mute_action.setText("\U0001f507 \u9759\u97f3\u6a21\u5f0f")

    def update_unread(self, count: int):
        self._unread_count = count
        pixmap = self._create_icon(count)
        self.setIcon(QIcon(pixmap))
