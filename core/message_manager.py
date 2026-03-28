import logging
from core import database
from core.signals import get_signals

logger = logging.getLogger("classpush.message_manager")


class MessageManager:
    def __init__(self):
        self.signals = get_signals()

    def send_message(self, msg_data: dict) -> int:
        msg_id = database.insert_message(msg_data)
        msg_data["id"] = msg_id
        self.signals.new_message.emit(msg_data)
        return msg_id

    def get_active_messages(self, limit=20, offset=0) -> list:
        return database.get_messages(status="active", limit=limit, offset=offset)

    def get_all_messages(self, limit=50, offset=0) -> list:
        return database.get_all_messages(limit=limit, offset=offset)

    def hide(self, msg_id: int):
        database.hide_message(msg_id)

    def unhide(self, msg_id: int):
        database.unhide_message(msg_id)

    def get_hidden_messages(self, limit=50) -> list:
        return database.get_hidden_messages(limit)

    def unhide_all(self):
        database.unhide_all_messages()

    def archive(self, msg_id: int):
        database.archive_message(msg_id)

    def delete(self, msg_id: int):
        database.delete_message(msg_id)

    def get_active_count(self) -> int:
        return database.get_active_count_no_hidden()

    def get_senders(self) -> list:
        return database.get_senders()

    def check_scheduled(self) -> list:
        return database.get_scheduled_messages()

    def expire_old(self, hours=24):
        database.expire_old_messages(hours)
