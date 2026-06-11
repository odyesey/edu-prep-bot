from aiogram.filters import BaseFilter, CommandObject
from aiogram.types import Message

from database import db
from utils.gettext import _

class Text(BaseFilter):
    def __init__(self, key: str) -> None:
        self.key = key

    async def __call__(self, message: Message) -> bool:
        lang = await db.lang(message.from_user.id)
        return message.text == _(self.key, lang)

class DeepLink(BaseFilter):
    async def __call__(self, message: Message, command: CommandObject) -> bool:
        return not command.args

class PositiveId(BaseFilter):
    async def __call__(self, message: Message, command: CommandObject) -> bool:
        try:
            return int(command.args) > 0
        except ValueError:
            return False
