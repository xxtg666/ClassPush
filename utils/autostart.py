import sys
import logging

logger = logging.getLogger("classpush.autostart")


def is_windows():
    return sys.platform == "win32"


def set_autostart(enable: bool):
    if not is_windows():
        logger.warning("Autostart only supported on Windows")
        return

    import winreg

    exe_path = sys.executable
    if hasattr(sys, "_MEIPASS"):
        exe_path = sys.executable

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        )
        if enable:
            winreg.SetValueEx(key, "ClassPush", 0, winreg.REG_SZ, f'"{exe_path}"')
            logger.info("Autostart enabled")
        else:
            try:
                winreg.DeleteValue(key, "ClassPush")
                logger.info("Autostart disabled")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logger.error("Failed to set autostart: %s", e)


def is_autostart_enabled() -> bool:
    if not is_windows():
        return False

    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, "ClassPush")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
