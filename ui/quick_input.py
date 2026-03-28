from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor


class QuickInput(QWidget):
    message_submitted = pyqtSignal(dict)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen_w = 1920
        screen_h = 1080
        w = int(screen_w * 0.5)
        h = 56
        self.setFixedSize(w, h)
        self.move((screen_w - w) // 2, int(screen_h * 0.3))

        self.container = QWidget(self)
        self.container.setFixedSize(w, h)
        self.container.setStyleSheet("""
            QWidget {
                background: rgba(255,255,255,0.95);
                border-radius: 28px;
                border: 1px solid rgba(255,255,255,0.5);
            }
        """)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(16, 4, 8, 4)
        layout.setSpacing(8)

        icon = QLabel("\U0001f50d")
        icon.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        layout.addWidget(icon)

        self.input = QLineEdit()
        self.input.setPlaceholderText(
            "\u8f93\u5165\u6d88\u606f\u5185\u5bb9\uff0c\u6309 Enter \u53d1\u9001..."
        )
        self.input.setStyleSheet("""
            QLineEdit {
                border: none; background: transparent;
                font-size: 16px; color: #333;
            }
        """)
        self.input.returnPressed.connect(self._submit)
        layout.addWidget(self.input)

        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("\u7c7b\u578b")
        self.type_input.setText("\u901a\u77e5")
        self.type_input.setFixedWidth(60)
        self.type_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0; border-radius: 8px;
                padding: 4px 8px; font-size: 13px; background: white;
            }
        """)
        layout.addWidget(self.type_input)

        send_btn = QPushButton("\u53d1\u9001 \u21a9")
        send_btn.setFixedSize(70, 40)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 20px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, stop:0 #7b93ed, stop:1 #8b5fbf);
            }
        """)
        send_btn.clicked.connect(self._submit)
        layout.addWidget(send_btn)

    def _submit(self):
        content = self.input.text().strip()
        if not content:
            return

        msg_type = self.type_input.text().strip() or "\u901a\u77e5"
        sender = self.config.get("user", {}).get("last_sender_name", "\u8001\u5e08")

        msg_data = {
            "type": msg_type,
            "sender": sender,
            "content": content,
            "duration_minutes": 0,
        }

        self.message_submitted.emit(msg_data)
        self.input.clear()
        self.hide()

    def show_quick(self):
        self.input.clear()
        self.show()
        self.activateWindow()
        self.input.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
