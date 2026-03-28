import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QDialog,
    QPlainTextEdit,
    QMessageBox,
    QPushButton,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt6.QtGui import QColor

from ui.sidebar_message_item import SidebarMessageItem
from core.signals import get_signals

logger = logging.getLogger("classpush.sidebar")

TYPE_COLORS = {
    "homework": "#FF6B6B",
    "notice": "#4ECDC4",
}

TYPE_DEFAULT_COLOR = "#667eea"


class MessageDetailDialog(QDialog):
    def __init__(self, msg_data: dict, message_manager, dark_mode=False, parent=None):
        super().__init__(parent)
        self.msg_data = msg_data
        self.mm = message_manager
        self.dark_mode = dark_mode
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("\u6d88\u606f\u8be6\u60c5")
        self.setFixedSize(500, 450)

        msg_type = self.msg_data.get("type", "\u901a\u77e5")
        type_color = TYPE_COLORS.get(msg_type, TYPE_DEFAULT_COLOR)
        type_label_text = msg_type

        bg = "#1e1e2e" if self.dark_mode else "#ffffff"
        text_color = "#cdd6f4" if self.dark_mode else "#1a1a2e"
        meta_color = "#a6adc8" if self.dark_mode else "#666"

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        badge = QLabel(type_label_text)
        badge.setFixedHeight(36)
        badge.setStyleSheet(f"""
            background: {type_color};
            color: white;
            border-radius: 10px;
            padding: 4px 16px;
            font-size: 15px;
            font-weight: bold;
        """)
        badge.setFixedWidth(badge.sizeHint().width() + 20)
        layout.addWidget(badge)

        sender = self.msg_data.get("sender", "\u8001\u5e08")
        sender_color = "#ffffff" if self.dark_mode else "#1a1a2e"
        sender_lbl = QLabel(sender)
        sender_lbl.setStyleSheet(
            f"color: {sender_color}; font-size: 22px; font-weight: bold;"
        )
        layout.addWidget(sender_lbl)

        created = self.msg_data.get("created_at", "")
        meta_lbl = QLabel(created)
        meta_lbl.setStyleSheet(f"color: {meta_color}; font-size: 13px;")
        layout.addWidget(meta_lbl)

        content = self.msg_data.get("content", "")
        body = QPlainTextEdit()
        body.setReadOnly(True)
        body.setPlainText(content)
        body.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {"rgba(255,255,255,0.05)" if self.dark_mode else "#f8f9fc"};
                border: 1px solid {"rgba(255,255,255,0.1)" if self.dark_mode else "#e8e8e8"};
                border-radius: 12px;
                padding: 16px;
                font-size: 18px;
                color: {text_color};
            }}
        """)
        layout.addWidget(body)

        btn_bar = QHBoxLayout()

        hide_btn = QPushButton("\U0001f5d2\ufe0f \u9690\u85cf\u6b64\u6d88\u606f")
        hide_btn.setFixedSize(140, 36)
        hide_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: #FF6B6B;
                border: 1px solid #FF6B6B;
                border-radius: 18px;
                font-size: 13px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: #FF6B6B;
                color: white;
            }}
        """)
        hide_btn.clicked.connect(self._on_hide)
        btn_bar.addWidget(hide_btn)
        btn_bar.addStretch()

        close_btn = QPushButton("\u5173\u95ed")
        close_btn.setFixedSize(80, 36)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {meta_color};
                border: 1px solid {meta_color};
                border-radius: 18px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {text_color};
                border-color: {text_color};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_bar.addWidget(close_btn)

        layout.addLayout(btn_bar)

    def _on_hide(self):
        reply = QMessageBox.question(
            self,
            "\u786e\u8ba4\u9690\u85cf",
            "\u786e\u5b9a\u8981\u9690\u85cf\u6b64\u6d88\u606f\u5417\uff1f\n\u53ef\u5728\u8bbe\u7f6e\u4e2d\u6062\u590d\u3002",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            msg_id = self.msg_data.get("id")
            if msg_id:
                self.mm.hide(msg_id)
            self.accept()


class SidebarPanel(QWidget):
    def __init__(self, message_manager, config: dict, parent=None):
        super().__init__(parent)
        self.mm = message_manager
        self.config = config
        self.signals = get_signals()
        self.dark_mode = config.get("display", {}).get("dark_mode", False)
        self.sidebar_pos = config.get("display", {}).get("sidebar_position", "right")
        self._is_visible = False
        self._slide_anim = None

        self._setup_ui()
        self._connect_signals()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(30000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()

        self.refresh()

    def _setup_ui(self):
        screen = self.screen()
        if screen:
            geo = screen.geometry()
            self._screen_w = geo.width()
            self._screen_h = geo.height()
        else:
            self._screen_w = 1920
            self._screen_h = 1080

        sidebar_pct = self.config.get("display", {}).get("sidebar_width_percent", 30)
        sidebar_w = max(400, min(560, int(self._screen_w * sidebar_pct / 100)))
        sidebar_h = int(self._screen_h * 0.85)
        y_pos = (self._screen_h - sidebar_h) // 2

        self.setFixedSize(sidebar_w, sidebar_h)

        bg = "rgba(24,24,37,0.90)" if self.dark_mode else "rgba(240,244,255,0.88)"
        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border-radius: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title_bar = QHBoxLayout()
        title_color = "#ffffff" if self.dark_mode else "#1a1a2e"
        class_name = self.config.get("user", {}).get("class_name", "\u73ed\u7ea7")
        title_lbl = QLabel(f"\U0001f4cb {class_name}\u6d88\u606f")
        title_lbl.setStyleSheet(
            f"color: {title_color}; font-size: 20px; font-weight: bold;"
        )
        title_bar.addWidget(title_lbl)

        self.count_badge = QLabel("0")
        self.count_badge.setFixedSize(28, 28)
        self.count_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_badge.setStyleSheet("""
            background: #FF3B30;
            color: white;
            border-radius: 14px;
            font-size: 12px;
            font-weight: bold;
        """)
        title_bar.addWidget(self.count_badge)
        title_bar.addStretch()

        layout.addLayout(title_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 6px;
                background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {"rgba(255,255,255,0.2)" if self.dark_mode else "rgba(0,0,0,0.15)"};
                border-radius: 3px;
            }}
        """)

        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_container)
        layout.addWidget(self.scroll_area)

        if self.sidebar_pos == "right":
            self._target_x = self._screen_w - sidebar_w - 16
        else:
            self._target_x = 16

        self.move(self._screen_w, y_pos)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _connect_signals(self):
        self.signals.new_message.connect(self._on_new_message)

    def _on_new_message(self, msg_data):
        self.refresh()

    def refresh(self):
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        messages = self.mm.get_active_messages(limit=20)
        self.count_badge.setText(str(len(messages)))

        for i, msg in enumerate(messages):
            item = SidebarMessageItem(msg, i, self.dark_mode, self)
            item.clicked.connect(self._on_item_clicked)
            self.scroll_layout.insertWidget(i, item)

    def _on_item_clicked(self, msg_data):
        dlg = MessageDetailDialog(msg_data, self.mm, self.dark_mode, self)
        dlg.exec()
        self.refresh()

    def show_sidebar(self):
        if self._is_visible:
            return
        self._is_visible = True
        self.refresh()
        y_pos = self.y()
        self.move(
            self._screen_w if self.sidebar_pos == "right" else -self.width(), y_pos
        )
        self.show()

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(300)
        self._slide_anim.setStartValue(
            QPoint(
                self._screen_w if self.sidebar_pos == "right" else -self.width(), y_pos
            )
        )
        self._slide_anim.setEndValue(QPoint(self._target_x, y_pos))
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

    def hide_sidebar(self):
        if not self._is_visible:
            return
        self._is_visible = False
        y_pos = self.y()

        self._slide_anim = QPropertyAnimation(self, b"pos")
        self._slide_anim.setDuration(300)
        self._slide_anim.setStartValue(QPoint(self._target_x, y_pos))
        self._slide_anim.setEndValue(
            QPoint(
                self._screen_w if self.sidebar_pos == "right" else -self.width(), y_pos
            )
        )
        self._slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._slide_anim.finished.connect(self.hide)
        self._slide_anim.start()

    def toggle(self):
        if self._is_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def update_config(self, config: dict):
        self.config = config
        self.dark_mode = config.get("display", {}).get("dark_mode", False)
