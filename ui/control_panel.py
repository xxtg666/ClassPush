import logging
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap

from ui.widgets.animated_button import AnimatedButton
from ui.widgets.toggle_switch import ToggleSwitch
from core.signals import get_signals
from utils import network

logger = logging.getLogger("classpush.control_panel")

DURATION_OPTIONS = [
    ("\u4e0d\u9650\u5236", 0),
    ("5\u5206\u949f", 5),
    ("1\u5c0f\u65f6", 60),
    ("12\u5c0f\u65f6", 720),
    ("\u81ea\u5b9a\u4e49", -1),
]


class SendPage(QWidget):
    message_sent = pyqtSignal(dict)

    def __init__(self, message_manager, config: dict, parent=None):
        super().__init__(parent)
        self.mm = message_manager
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("\u53d1\u9001\u65b0\u6d88\u606f")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("\u6d88\u606f\u7c7b\u578b"))
        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText(
            "\u8f93\u5165\u6d88\u606f\u7c7b\u578b\uff0c\u5982\uff1a\u4f5c\u4e1a\u3001\u901a\u77e5"
        )
        self.type_input.setStyleSheet(self._input_style())
        type_layout.addWidget(self.type_input)
        layout.addLayout(type_layout)

        sender_layout = QVBoxLayout()
        sender_layout.addWidget(QLabel("\u53d1\u9001\u4eba"))
        self.sender_input = QLineEdit()
        last_sender = self.config.get("user", {}).get(
            "last_sender_name", "\u8001\u5e08"
        )
        self.sender_input.setText(last_sender)
        self.sender_input.setPlaceholderText("\u60a8\u7684\u79f0\u547c")
        self.sender_input.setStyleSheet(self._input_style())
        sender_layout.addWidget(self.sender_input)
        layout.addLayout(sender_layout)

        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("\u6d88\u606f\u5185\u5bb9"))
        self.content_input = QPlainTextEdit()
        self.content_input.setPlaceholderText(
            "\u5728\u6b64\u8f93\u5165\u6d88\u606f\u5185\u5bb9\uff0c\u652f\u6301\u591a\u884c\u3002Ctrl+Enter \u5feb\u901f\u53d1\u9001"
        )
        self.content_input.setFixedHeight(150)
        self.content_input.setStyleSheet("""
            QPlainTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 16px;
                background: white;
                selection-background-color: #4361ee;
            }
            QPlainTextEdit:focus { border-color: #4361ee; }
        """)
        content_layout.addWidget(self.content_input)

        self.char_count = QLabel("0/500")
        self.char_count.setStyleSheet("color: #999; font-size: 12px;")
        self.char_count.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.content_input.textChanged.connect(self._update_char_count)
        content_layout.addWidget(self.char_count)
        layout.addLayout(content_layout)

        dur_layout = QHBoxLayout()
        dur_layout.addWidget(QLabel("\u663e\u793a\u65f6\u95f4:"))
        self.duration_combo = QComboBox()
        for label, mins in DURATION_OPTIONS:
            self.duration_combo.addItem(label, mins)
        self.duration_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #e0e0e0; border-radius: 10px;
                padding: 8px 16px; font-size: 14px; background: white; min-width: 120px;
            }
            QComboBox:focus { border-color: #4361ee; }
        """)
        self.duration_combo.currentIndexChanged.connect(self._on_duration_changed)
        dur_layout.addWidget(self.duration_combo)

        self.custom_minutes = QSpinBox()
        self.custom_minutes.setRange(1, 1440)
        self.custom_minutes.setValue(30)
        self.custom_minutes.setSuffix("\u5206\u949f")
        self.custom_minutes.setVisible(False)
        self.custom_minutes.setStyleSheet(self._input_style())
        dur_layout.addWidget(self.custom_minutes)
        dur_layout.addStretch()
        layout.addLayout(dur_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.send_btn = AnimatedButton("\U0001f4e4 \u53d1\u9001")
        self.send_btn.setFixedSize(160, 48)
        self.send_btn.clicked.connect(self._send_message)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        layout.addStretch()

    def _on_duration_changed(self, index):
        self.custom_minutes.setVisible(DURATION_OPTIONS[index][1] == -1)

    def _input_style(self):
        return """
            QLineEdit {
                border: 2px solid #e0e0e0; border-radius: 10px;
                padding: 8px 16px; font-size: 15px; background: white;
            }
            QLineEdit:focus { border-color: #4361ee; }
        """

    def _update_char_count(self):
        length = len(self.content_input.toPlainText())
        self.char_count.setText(f"{length}/500")
        self.char_count.setStyleSheet(
            "color: #FF3B30; font-size: 12px;"
            if length > 500
            else "color: #999; font-size: 12px;"
        )

    def _send_message(self):
        content = self.content_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(
                self, "\u63d0\u793a", "\u8bf7\u8f93\u5165\u6d88\u606f\u5185\u5bb9"
            )
            return
        if len(content) > 500:
            QMessageBox.warning(
                self,
                "\u63d0\u793a",
                "\u6d88\u606f\u5185\u5bb9\u4e0d\u80fd\u8d85\u8fc7500\u5b57",
            )
            return

        duration = self.duration_combo.currentData()
        if duration == -1:
            duration = self.custom_minutes.value()

        msg_type = self.type_input.text().strip() or "\u901a\u77e5"
        msg_data = {
            "type": msg_type,
            "sender": self.sender_input.text().strip() or "\u8001\u5e08",
            "content": content,
            "duration_minutes": duration,
        }

        self.message_sent.emit(msg_data)
        self.send_btn.setText("\u2713 \u5df2\u53d1\u9001")
        self.send_btn.set_gradient("#27ae60", "#2ecc71")
        QTimer.singleShot(
            1500,
            lambda: (
                self.send_btn.setText("\U0001f4e4 \u53d1\u9001"),
                self.send_btn.set_gradient("#667eea", "#764ba2"),
            ),
        )

        self.content_input.clear()

        user_cfg = self.config.get("user", {})
        user_cfg["last_sender_name"] = msg_data["sender"]
        history = user_cfg.get("sender_history", [])
        if msg_data["sender"] not in history:
            history.append(msg_data["sender"])
            user_cfg["sender_history"] = history[-20:]


class HistoryPage(QWidget):
    def __init__(self, message_manager, parent=None):
        super().__init__(parent)
        self.mm = message_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("\U0001f4cb \u5386\u53f2\u6d88\u606f")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #e8e8e8; border-radius: 12px;
                background: white; font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 16px; border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover { background: #f8f9fc; }
        """)
        layout.addWidget(self.list_widget)
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        messages = self.mm.get_all_messages(limit=50)
        for msg in messages:
            msg_type = msg.get("type", "\u901a\u77e5")
            sender = msg.get("sender", "")
            content = msg.get("content", "")
            created = msg.get("created_at", "")
            status = msg.get("status", "")
            hidden = msg.get("hidden", 0)
            status_str = "\U0001f7e2" if status == "active" and not hidden else "\u26ab"
            dur = msg.get("duration_minutes", 0)
            dur_str = f" [{dur}\u5206]" if dur > 0 else ""

            text = f"{status_str} [{msg_type}] {sender}: {content[:35]}{'...' if len(content) > 35 else ''}  {created[:16]}{dur_str}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, msg.get("id"))
            self.list_widget.addItem(item)


class SettingsPage(QWidget):
    config_changed = pyqtSignal(dict)

    def __init__(self, config: dict, message_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.mm = message_manager
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("\u2699\ufe0f \u8bbe\u7f6e")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        display_grp = QLabel("\U0001f4fa \u663e\u793a\u8bbe\u7f6e")
        display_grp.setStyleSheet("font-size: 16px; font-weight: bold; color: #4361ee;")
        layout.addWidget(display_grp)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("\u6d88\u606f\u5b57\u4f53\u5927\u5c0f:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(16, 48)
        self.font_spin.setValue(self.config.get("display", {}).get("font_size", 28))
        self.font_spin.setSuffix("px")
        font_layout.addWidget(self.font_spin)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        auto_close_layout = QHBoxLayout()
        auto_close_layout.addWidget(QLabel("\u5f39\u7a97\u81ea\u52a8\u5173\u95ed:"))
        self.auto_close_spin = QSpinBox()
        self.auto_close_spin.setRange(3, 120)
        self.auto_close_spin.setValue(
            self.config.get("display", {}).get("auto_close_seconds", 30)
        )
        self.auto_close_spin.setSuffix("\u79d2")
        auto_close_layout.addWidget(self.auto_close_spin)
        auto_close_layout.addStretch()
        layout.addLayout(auto_close_layout)

        dark_layout = QHBoxLayout()
        dark_layout.addWidget(QLabel("\u6df1\u8272\u6a21\u5f0f:"))
        self.dark_toggle = ToggleSwitch()
        self.dark_toggle.set_checked(
            self.config.get("display", {}).get("dark_mode", False)
        )
        dark_layout.addWidget(self.dark_toggle)
        dark_layout.addStretch()
        layout.addLayout(dark_layout)

        layout.addSpacing(8)
        notif_grp = QLabel("\U0001f514 \u63d0\u9192\u8bbe\u7f6e")
        notif_grp.setStyleSheet("font-size: 16px; font-weight: bold; color: #4361ee;")
        layout.addWidget(notif_grp)

        sound_layout = QHBoxLayout()
        sound_layout.addWidget(QLabel("\u63d0\u793a\u97f3:"))
        self.sound_toggle = ToggleSwitch()
        self.sound_toggle.set_checked(
            self.config.get("notification", {}).get("sound_enabled", True)
        )
        sound_layout.addWidget(self.sound_toggle)
        sound_layout.addStretch()
        layout.addLayout(sound_layout)

        layout.addSpacing(8)
        net_grp = QLabel("\U0001f310 \u7f51\u7edc\u8bbe\u7f6e")
        net_grp.setStyleSheet("font-size: 16px; font-weight: bold; color: #4361ee;")
        layout.addWidget(net_grp)

        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(QLabel("WebUI\u5bc6\u7801:"))
        self.pwd_input = QLineEdit()
        current_pwd = self.config.get("network", {}).get("password", "")
        self.pwd_input.setText(current_pwd or "")
        self.pwd_input.setPlaceholderText("\u7559\u7a7a\u8868\u793a\u65e0\u5bc6\u7801")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setStyleSheet(self._input_style())
        self.pwd_input.setFixedWidth(200)
        pwd_layout.addWidget(self.pwd_input)
        pwd_layout.addStretch()
        layout.addLayout(pwd_layout)

        layout.addSpacing(8)
        hidden_grp = QLabel("\U0001f5d2\ufe0f \u9690\u85cf\u6d88\u606f")
        hidden_grp.setStyleSheet("font-size: 16px; font-weight: bold; color: #4361ee;")
        layout.addWidget(hidden_grp)

        hidden_count = len(self.mm.get_hidden_messages())
        hidden_info = QLabel(
            f"\u5f53\u524d\u6709 {hidden_count} \u6761\u9690\u85cf\u6d88\u606f"
        )
        hidden_info.setStyleSheet("color: #666; font-size: 13px;")
        layout.addWidget(hidden_info)

        restore_btn = QPushButton("\u6062\u590d\u6240\u6709\u9690\u85cf\u6d88\u606f")
        restore_btn.setFixedSize(150, 36)
        restore_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #4361ee; border: 1px solid #4361ee;
                border-radius: 18px; font-size: 13px; padding: 6px 16px;
            }
            QPushButton:hover { background: #4361ee; color: white; }
        """)
        restore_btn.clicked.connect(self._restore_hidden)
        layout.addWidget(restore_btn)

        layout.addStretch()

        save_btn = AnimatedButton("\u4fdd\u5b58\u8bbe\u7f6e")
        save_btn.setFixedSize(160, 44)
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _input_style(self):
        return """
            QLineEdit {
                border: 2px solid #e0e0e0; border-radius: 10px;
                padding: 8px 16px; font-size: 14px; background: white;
            }
            QLineEdit:focus { border-color: #4361ee; }
        """

    def _restore_hidden(self):
        hidden = self.mm.get_hidden_messages()
        if not hidden:
            QMessageBox.information(
                self, "\u63d0\u793a", "\u6ca1\u6709\u9690\u85cf\u7684\u6d88\u606f"
            )
            return
        reply = QMessageBox.question(
            self,
            "\u786e\u8ba4",
            f"\u786e\u5b9a\u8981\u6062\u590d {len(hidden)} \u6761\u9690\u85cf\u6d88\u606f\u5417\uff1f",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.mm.unhide_all()
            QMessageBox.information(
                self,
                "\u63d0\u793a",
                "\u5df2\u6062\u590d\u6240\u6709\u9690\u85cf\u6d88\u606f",
            )

    def _save(self):
        self.config.setdefault("display", {})["font_size"] = self.font_spin.value()
        self.config.setdefault("display", {})["auto_close_seconds"] = (
            self.auto_close_spin.value()
        )
        self.config.setdefault("display", {})["dark_mode"] = (
            self.dark_toggle.is_checked()
        )
        self.config.setdefault("notification", {})["sound_enabled"] = (
            self.sound_toggle.is_checked()
        )
        pwd = self.pwd_input.text().strip()
        self.config.setdefault("network", {})["password"] = pwd if pwd else None
        self.config_changed.emit(self.config)


class QRCodePage(QWidget):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        title = QLabel("\U0001f4f1 \u624b\u673a\u53d1\u9001")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        desc = QLabel(
            "\u8f93\u5165\u94fe\u63a5\u751f\u6210\u4e8c\u7ef4\u7801\uff0c\u624b\u673a\u626b\u7801\u5373\u53ef\u53d1\u6d88\u606f\u3002"
        )
        desc.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(desc)

        link_layout = QHBoxLayout()
        self.link_input = QLineEdit()
        saved_link = self.config.get("web", {}).get("saved_link", "")
        if not saved_link:
            ip = network.get_primary_ip()
            port = self.config.get("network", {}).get("port", 8080)
            saved_link = f"http://{ip}:{port}"
        self.link_input.setText(saved_link)
        self.link_input.setPlaceholderText("\u8f93\u5165\u7f51\u9875\u5730\u5740...")
        self.link_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0; border-radius: 10px;
                padding: 8px 16px; font-size: 14px; background: white;
            }
            QLineEdit:focus { border-color: #4361ee; }
        """)
        link_layout.addWidget(self.link_input)

        gen_btn = QPushButton("\u751f\u6210")
        gen_btn.setFixedSize(80, 40)
        gen_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 10px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, stop:0 #7b93ed, stop:1 #8b5fbf);
            }
        """)
        gen_btn.clicked.connect(self._generate_qr)
        link_layout.addWidget(gen_btn)
        layout.addLayout(link_layout)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setFixedSize(250, 250)
        layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.url_label = QLabel()
        self.url_label.setStyleSheet(
            "font-size: 14px; color: #4361ee; font-weight: bold;"
        )
        self.url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.url_label)

        layout.addStretch()
        self._generate_qr()

    def _generate_qr(self):
        url = self.link_input.text().strip()
        if not url:
            return

        self.config.setdefault("web", {})["saved_link"] = url
        self.url_label.setText(url)

        try:
            from utils.qrcode_gen import generate_qrcode
            from PyQt6.QtGui import QImage
            import io

            img = generate_qrcode(url, box_size=6)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            qimg = QImage.fromData(data)
            pixmap = QPixmap.fromImage(qimg)
            self.qr_label.setPixmap(
                pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
            )
        except Exception as e:
            self.qr_label.setText(f"\u4e8c\u7ef4\u7801\u751f\u6210\u5931\u8d25: {e}")


class ControlPanel(QWidget):
    message_sent = pyqtSignal(dict)
    config_saved = pyqtSignal(dict)

    def __init__(self, message_manager, config: dict, parent=None):
        super().__init__(parent)
        self.mm = message_manager
        self.config = config
        self._setup_ui()
        self._setup_window()

    def _setup_window(self):
        self.setWindowTitle("ClassPush \u63a7\u5236\u53f0")
        self.setFixedSize(900, 640)
        self.setStyleSheet("background: #f8f9fc;")

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        nav_widget = QWidget()
        nav_widget.setFixedWidth(200)
        nav_widget.setStyleSheet(
            "background: #ffffff; border-right: 1px solid #e8e8e8;"
        )
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 16, 0, 16)
        nav_layout.setSpacing(4)

        logo = QLabel("\U0001f514 ClassPush")
        logo.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #4361ee; padding: 0 20px;"
        )
        logo.setFixedHeight(40)
        nav_layout.addWidget(logo)
        nav_layout.addSpacing(12)

        nav_items = [
            ("\U0001f4dd \u53d1\u6d88\u606f", 0),
            ("\U0001f4cb \u5386\u53f2", 1),
            ("\u2699\ufe0f \u8bbe\u7f6e", 2),
            ("\U0001f4f1 \u624b\u673a\u53d1\u9001", 3),
        ]

        self.nav_buttons = []
        for text, idx in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(44)
            btn.setStyleSheet("""
                QPushButton {
                    border: none; text-align: left; padding: 0 20px;
                    font-size: 15px; color: #555; background: transparent;
                    border-left: 3px solid transparent;
                }
                QPushButton:hover { background: #f5f5f5; }
                QPushButton:checked {
                    background: #eef2ff; border-left: 3px solid #4361ee;
                    color: #4361ee; font-weight: bold;
                }
            """)
            btn.clicked.connect(lambda checked, i=idx: self._switch_page(i))
            nav_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        self.nav_buttons[0].setChecked(True)
        nav_layout.addStretch()
        layout.addWidget(nav_widget)

        self.stack = QStackedWidget()

        self.send_page = SendPage(self.mm, self.config)
        self.send_page.message_sent.connect(self._on_message_sent)
        self.stack.addWidget(self.send_page)

        self.history_page = HistoryPage(self.mm)
        self.stack.addWidget(self.history_page)

        self.settings_page = SettingsPage(self.config, self.mm)
        self.settings_page.config_changed.connect(self._on_config_changed)
        self.stack.addWidget(self.settings_page)

        self.qrcode_page = QRCodePage(self.config)
        self.stack.addWidget(self.qrcode_page)

        layout.addWidget(self.stack)

    def _switch_page(self, index):
        for btn in self.nav_buttons:
            btn.setChecked(False)
        self.nav_buttons[index].setChecked(True)
        self.stack.setCurrentIndex(index)
        if index == 1:
            self.history_page.refresh()

    def _on_message_sent(self, msg_data):
        self.message_sent.emit(msg_data)

    def _on_config_changed(self, config):
        self.config = config
        self.config_saved.emit(config)
