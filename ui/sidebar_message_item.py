from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

TYPE_COLORS = {
    "homework": "#FF6B6B",
    "notice": "#4ECDC4",
}

TYPE_DEFAULT_COLOR = "#667eea"


class SidebarMessageItem(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, msg_data: dict, index: int, dark_mode=False, parent=None):
        super().__init__(parent)
        self.msg_data = msg_data
        self.dark_mode = dark_mode
        self._setup_ui(index)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _setup_ui(self, index):
        msg_type = self.msg_data.get("type", "\u901a\u77e5")
        type_color = TYPE_COLORS.get(msg_type, TYPE_DEFAULT_COLOR)

        bg = "rgba(49,50,68,0.9)" if self.dark_mode else "#ffffff"
        border_color = "rgba(255,255,255,0.08)" if self.dark_mode else "#f0f0f0"
        title_color = "#ffffff" if self.dark_mode else "#666"
        body_color = "#a6adc8" if self.dark_mode else "#1a1a2e"
        meta_color = "#6c7086" if self.dark_mode else "#999"

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            QFrame:hover {{
                background: {"rgba(69,70,90,0.9)" if self.dark_mode else "#f8f9fc"};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(10)

        num_lbl = QLabel(str(index + 1))
        num_lbl.setFixedSize(36, 36)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setStyleSheet(f"""
            background: {type_color};
            color: white;
            border-radius: 18px;
            font-size: 16px;
            font-weight: bold;
        """)
        header.addWidget(num_lbl)

        type_lbl = QLabel(msg_type)
        type_lbl.setStyleSheet(
            f"color: {type_color}; font-size: 13px; font-weight: bold;"
        )
        header.addWidget(type_lbl)
        header.addStretch()

        created = self.msg_data.get("created_at", "")
        if created and len(created) > 16:
            created = created[11:16]
        meta_lbl = QLabel(created)
        meta_lbl.setStyleSheet(f"color: {meta_color}; font-size: 12px;")
        header.addWidget(meta_lbl)

        layout.addLayout(header)

        sender = self.msg_data.get("sender", "\u8001\u5e08")
        sender_lbl = QLabel(sender)
        sender_lbl.setStyleSheet(
            f"color: {title_color}; font-size: 15px; font-weight: bold;"
        )
        layout.addWidget(sender_lbl)

        content = self.msg_data.get("content", "")
        preview = content[:60] + ("..." if len(content) > 60 else "")
        body_lbl = QLabel(preview)
        body_lbl.setStyleSheet(f"color: {body_color}; font-size: 16px;")
        body_lbl.setWordWrap(True)
        body_lbl.setMaximumWidth(350)
        layout.addWidget(body_lbl)

        self.setFixedHeight(self.sizeHint().height())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.msg_data)
