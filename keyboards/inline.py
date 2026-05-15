from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.gettext import locales, _

def auto_detected_lang(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("select_detected_lang", lang), callback_data="lang_"+lang)],
        [InlineKeyboardButton(text=_("select_other_lang", lang), callback_data="lang_menu")]
    ])

def lang_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for lang in locales:
        builder.button(text=_("name", lang), callback_data="lang_"+lang)

    builder.adjust(1)
    return builder.as_markup()

def yes_no(lang: str, prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("no_", lang), callback_data=prefix + "no"),
        InlineKeyboardButton(text=_("yes_", lang), callback_data=prefix+"yes")]
    ])

def resources_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("add_resource", lang), callback_data="resources_add")],
    ])

def verify_button(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("start_verify", lang), callback_data="verify")]
    ])
