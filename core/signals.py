from PyQt6.QtCore import QObject, pyqtSignal


class GlobalSignals(QObject):
    new_message = pyqtSignal(dict)
    config_changed = pyqtSignal(dict)
    show_overlay = pyqtSignal(dict)
    hide_overlay = pyqtSignal()
    show_sidebar = pyqtSignal()
    hide_sidebar = pyqtSignal()
    tray_activated = pyqtSignal(int)
    web_server_started = pyqtSignal(str, int)


_signals_instance = None


def get_signals() -> GlobalSignals:
    global _signals_instance
    if _signals_instance is None:
        _signals_instance = GlobalSignals()
    return _signals_instance
