import sys
import os
import logging
import threading
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from waitress import serve

logger = logging.getLogger("classpush.app")


class WebServerThread(threading.Thread):
    def __init__(self, app, host, port):
        super().__init__(daemon=True)
        self.app = app
        self.host = host
        self.port = port
        self.server = None

    def run(self):
        try:
            logger.info("Starting web server on %s:%d", self.host, self.port)
            serve(self.app, host=self.host, port=self.port, threads=4)
        except Exception as e:
            logger.error("Web server error: %s", e)


class ClassPushApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ClassPush")
        self.app.setQuitOnLastWindowClosed(False)

        from utils.logger import setup_logging

        setup_logging()

        from utils.single_instance import SingleInstance

        self._instance = SingleInstance()
        if self._instance.is_running():
            logger.warning("Another instance is already running")
            sys.exit(0)

        from core import database

        database.init_database()

        from core.config_manager import load_config

        self.config = load_config()

        from core.message_manager import MessageManager

        self.mm = MessageManager()

        from core.signals import get_signals

        self.signals = get_signals()

        from core.scheduler import Scheduler

        self.scheduler = Scheduler(self.mm, self.config)

        self._setup_web_server()
        self._setup_ui()
        self._setup_connections()
        self._is_muted = False

    def _setup_web_server(self):
        from web.server import create_app
        from utils import network

        port = self.config.get("network", {}).get("port", 8080)
        try:
            from utils.network import find_available_port

            port = find_available_port(port)
        except RuntimeError:
            logger.warning("Could not find available port, using %d", port)

        self.config.setdefault("network", {})["port"] = port
        flask_app = create_app(self.mm, self.config)

        self.web_thread = WebServerThread(flask_app, "0.0.0.0", port)
        self.web_thread.start()

        ips = network.get_local_ips()
        if ips:
            logger.info("Web interface available at http://%s:%d", ips[0], port)
        self.signals.web_server_started.emit(network.get_primary_ip(), port)

    def _setup_ui(self):
        from ui.overlay_window import OverlayWindow
        from ui.sidebar_panel import SidebarPanel
        from ui.control_panel import ControlPanel
        from ui.tray_icon import TrayIcon
        from ui.quick_input import QuickInput

        self.overlay = OverlayWindow(self.config)
        self.sidebar = SidebarPanel(self.mm, self.config)
        self.control_panel = ControlPanel(self.mm, self.config)
        self.quick_input = QuickInput(self.config)

        self.tray = TrayIcon()
        self.tray.show()

        self.sidebar.show_sidebar()

        if self.config.get("general", {}).get("first_run", True):
            self.config["general"]["first_run"] = False
            from core.config_manager import save_config

            save_config(self.config)

    def _setup_connections(self):
        self.signals.new_message.connect(self._on_new_message)
        self.signals.show_overlay.connect(self.overlay.show_message)
        self.signals.show_sidebar.connect(self.sidebar.show_sidebar)
        self.signals.hide_sidebar.connect(self.sidebar.hide_sidebar)

        self.tray.show_panel_requested.connect(self._show_control_panel)
        self.tray.toggle_sidebar_requested.connect(self.sidebar.toggle)
        self.tray.quit_requested.connect(self._quit)
        self.tray.mute_toggled.connect(self._on_mute_toggled)

        self.control_panel.message_sent.connect(self.mm.send_message)
        self.control_panel.config_saved.connect(self._on_config_saved)
        self.quick_input.message_submitted.connect(self.mm.send_message)

        self.scheduler.start()

        self._unread_timer = QTimer()
        self._unread_timer.setInterval(2000)
        self._unread_timer.timeout.connect(self._update_unread_count)
        self._unread_timer.start()

    def _on_new_message(self, msg_data):
        sound_enabled = self.config.get("notification", {}).get("sound_enabled", True)
        if sound_enabled and not self._is_muted:
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                try:
                    QApplication.beep()
                except Exception:
                    pass

        sender = msg_data.get("sender", "")
        content = msg_data.get("content", "")
        preview = content[:30] + ("..." if len(content) > 30 else "")
        self.tray.showMessage(
            "ClassPush",
            f"{sender}: {preview}",
            self.tray.MessageIcon.Information,
            5000,
        )

        self.overlay.show_message(msg_data)
        self.sidebar.refresh()

    def _show_control_panel(self):
        self.control_panel.show()
        self.control_panel.activateWindow()
        self.control_panel.raise_()

    def _on_mute_toggled(self, muted):
        self._is_muted = muted
        logger.info("Mute toggled: %s", muted)

    def _on_config_saved(self, config):
        from core.config_manager import save_config

        self.config = config
        save_config(config)
        self.overlay.update_config(config)
        self.sidebar.update_config(config)

    def _update_unread_count(self):
        count = self.mm.get_active_count()
        self.tray.update_unread(count)

    def _quit(self):
        self.scheduler.stop()
        self.tray.hide()
        self.overlay.close()
        self.sidebar.close()
        self.control_panel.close()
        self.quick_input.close()
        self.app.quit()

    def run(self):
        logger.info("ClassPush started")
        return self.app.exec()
