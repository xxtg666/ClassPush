import logging
from PyQt6.QtCore import QTimer, QObject
from core.message_manager import MessageManager
from core.signals import get_signals

logger = logging.getLogger("classpush.scheduler")


class Scheduler(QObject):
    def __init__(self, message_manager: MessageManager, config: dict):
        super().__init__()
        self.mm = message_manager
        self.config = config
        self.signals = get_signals()

        self.check_timer = QTimer(self)
        self.check_timer.setInterval(5000)
        self.check_timer.timeout.connect(self._check_scheduled)

        self.expire_timer = QTimer(self)
        self.expire_timer.setInterval(60000)
        self.expire_timer.timeout.connect(self._expire_old)

    def start(self):
        self.check_timer.start()
        self.expire_timer.start()
        logger.info("Scheduler started")

    def stop(self):
        self.check_timer.stop()
        self.expire_timer.stop()
        logger.info("Scheduler stopped")

    def _check_scheduled(self):
        try:
            msgs = self.mm.check_scheduled()
            for msg in msgs:
                if msg.get("status") == "active":
                    self.signals.new_message.emit(msg)
        except Exception as e:
            logger.error("Error checking scheduled messages: %s", e)

    def _expire_old(self):
        try:
            self.mm.expire_old(24)
        except Exception as e:
            logger.error("Error expiring old messages: %s", e)
