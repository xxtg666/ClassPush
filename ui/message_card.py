from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.widgets.animated_button import AnimatedButton
from ui.widgets.progress_bar import CountdownProgressBar

TYPE_COLORS = {
    "homework": "#FF6B6B",
    "notice": "#4ECDC4",
}

TYPE_DEFAULT_COLOR = "#667eea"


class MessageCard(QWidget):
    dismissed = pyqtSignal()

    def __init__(self, msg_data: dict, font_size=28, dark_mode=False, parent=None):
        super().__init__(parent)
        self.msg_data = msg_data
        self.font_size = font_size
        self.dark_mode = dark_mode
        self._setup_ui()
        self._apply_shadow()

    def _setup_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )

        card_width = 700
        self.setFixedWidth(card_width)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.card_container = QWidget()
        bg = "rgba(30,30,46,0.92)" if self.dark_mode else "rgba(255,255,255,0.92)"
        self.card_container.setStyleSheet(f"""
            background: {bg};
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.3);
        """)

        card_layout = QVBoxLayout(self.card_container)
        card_layout.setContentsMargins(0, 0, 0, 20)
        card_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(64)
        msg_type = self.msg_data.get("type", "notice")
        type_color = TYPE_COLORS.get(msg_type, TYPE_COLORS["notice"])
        title_bar.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, stop:0 #667eea, stop:1 #764ba2);
            border-radius: 20px 20px 0 0;
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(24, 0, 20, 0)

        title_label = QLabel(f"\U0001f514  新消息提醒")
        title_label.setStyleSheet(
            "color: white; font-size: 20px; font-weight: bold; background: transparent;"
        )
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        close_btn = QLabel("\u2715")
        close_btn.setFixedSize(36, 36)
        close_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        close_btn.setStyleSheet("""
            QLabel {
                color: white; font-size: 18px; background: rgba(255,255,255,0.15);
                border-radius: 18px;
            }
            QLabel:hover { background: rgba(255,59,48,0.8); }
        """)
        close_btn.mousePressEvent = lambda ev: self.dismissed.emit()
        title_bar_layout.addWidget(close_btn)

        card_layout.addWidget(title_bar)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(32, 20, 32, 16)
        content_layout.setSpacing(12)

        type_text = self.msg_data.get("type", "\u901a\u77e5")
        type_color = TYPE_COLORS.get(type_text, TYPE_DEFAULT_COLOR)
        badge = QLabel(type_text)
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
        content_layout.addWidget(badge)

        sender = self.msg_data.get("sender", "\u8001\u5e08")
        created = self.msg_data.get("created_at", "")
        if created and len(created) > 16:
            created = created[11:16]

        sender_color = "#ffffff" if self.dark_mode else "#1a1a2e"
        sender_lbl = QLabel(sender)
        sender_lbl.setStyleSheet(
            f"color: {sender_color}; font-size: 18px; font-weight: bold;"
        )
        content_layout.addWidget(sender_lbl)

        meta_color = "#a6adc8" if self.dark_mode else "#999"
        meta_lbl = QLabel(created)
        meta_lbl.setStyleSheet(f"color: {meta_color}; font-size: 14px;")
        content_layout.addWidget(meta_lbl)

        content_text = self.msg_data.get("content", "")
        body_lbl = QLabel(content_text)
        body_color = "#cdd6f4" if self.dark_mode else "#2d3436"
        body_lbl.setStyleSheet(f"""
            color: {body_color};
            font-size: {self.font_size}px;
            font-weight: bold;
            line-height: 1.8;
        """)
        body_lbl.setWordWrap(True)
        body_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        content_layout.addWidget(body_lbl)

        content_layout.addSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.dismiss_btn = AnimatedButton("\u77e5\u9053\u4e86 \u2713")
        self.dismiss_btn.setFixedSize(180, 52)
        self.dismiss_btn.clicked.connect(self.dismissed.emit)
        btn_layout.addWidget(self.dismiss_btn)
        btn_layout.addStretch()
        content_layout.addLayout(btn_layout)

        card_layout.addWidget(content_widget)

        self.progress_bar = CountdownProgressBar(parent=self.card_container)
        card_layout.addWidget(self.progress_bar)

        main_layout.addWidget(self.card_container)
        self.adjustSize()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 20)
        self.card_container.setGraphicsEffect(shadow)

    def start_countdown(self, seconds=8, callback=None):
        def on_finish():
            if callback:
                callback()
            self.dismissed.emit()

        self.progress_bar.set_finished_callback(on_finish)
        self.progress_bar.start(seconds)

    def stop_countdown(self):
        self.progress_bar.stop()
