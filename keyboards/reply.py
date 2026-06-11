from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestChat

from utils.gettext import _

def start_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=_("tests", lang)), KeyboardButton(text=_("resources", lang))],
        [KeyboardButton(text=_("vocabulary", lang)), KeyboardButton(text=_("leaderboard", lang))],
        [KeyboardButton(text=_("profile", lang)), KeyboardButton(text=_("change_lang", lang))]
    ], resize_keyboard=True)

def tests_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=_("host_test", lang)), KeyboardButton(text=_("join_test", lang))],
        [KeyboardButton(text=_("previous_results", lang)), KeyboardButton(text=_("back", lang))]
    ], resize_keyboard=True)

def vocabulary_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=_("vocabulary_add", lang)), KeyboardButton(text=_("continue", lang))],
        [KeyboardButton(text=_("saved_btn", lang)), KeyboardButton(text=_("search", lang))],
        [KeyboardButton(text=_("back", lang))]
    ], resize_keyboard=True)

def channels_list(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=_("send_channel", lang), request_chat=KeyboardButtonRequestChat(
            request_id=0,
            chat_is_channel=True
        ))],
         [KeyboardButton(text=_("cancel", lang), style="danger")]
    ], resize_keyboard=True)

def cancel_button(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=_("cancel", lang), style="danger")]
    ], resize_keyboard=True)
