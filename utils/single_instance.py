import sys
import logging

logger = logging.getLogger("classpush.single_instance")


class SingleInstance:
    def __init__(self):
        self.mutex = None
        self.already_running = False

        if sys.platform == "win32":
            import ctypes

            self.mutex = ctypes.windll.kernel32.CreateMutexW(
                None, False, "ClassPush_SingleInstance_Mutex"
            )
            self.already_running = ctypes.windll.kernel32.GetLastError() == 183

    def is_running(self) -> bool:
        return self.already_running

    def release(self):
        if self.mutex and sys.platform == "win32":
            import ctypes

            ctypes.windll.kernel32.CloseHandle(self.mutex)
            self.mutex = None
