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

def active_test_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("test_submit_answers", lang), callback_data="submit")],
        [InlineKeyboardButton(text=_("refresh", lang), callback_data="refresh")],
    ])

def resources_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("add_resource", lang), callback_data="resources_add")],
        [InlineKeyboardButton(text=_("saved_btn", lang), callback_data="resource_saves_1")],
    ])

def pagination(lang: str, page: int, max_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = [[]]
    if page > 1: buttons[0].append(InlineKeyboardButton(text=_("prev", lang), callback_data=prefix + str(page - 1)))
    if page < max_pages: buttons[0].append(InlineKeyboardButton(text=_("next", lang), callback_data=prefix + str(page + 1)))
    buttons.append([InlineKeyboardButton(text=_("resources", lang), callback_data="resources")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def save_resource(lang: str, resource_id: int, delete: bool = False) -> InlineKeyboardMarkup:
    mode = 0
    text = _("resource_save", lang)
    if delete:
        mode = 1
        text = _("resource_delete", lang)

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"save_{mode}_{resource_id}")],
    ])

def vocab_button(lang: str, vocab_id: int, continue_: bool) -> InlineKeyboardMarkup:
    if continue_: text = _("continue", lang)
    else: text = _("begin", lang)

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"vocab_{vocab_id}")]
    ])

def vocab_learning_keyboard(lang: str, finished: bool = False):
    buttons = []

    text = _("incorrect", lang)
    callback_data = "word_-1"
    if finished:
        text = _("restart", lang)
        callback_data = "word_0"
    else:
        buttons.append(InlineKeyboardButton(text=_("correct", lang), callback_data="word_1"))

    buttons.insert(0, InlineKeyboardButton(text=text, callback_data=callback_data))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def verify_button(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("start_verify", lang), callback_data="verify")]
    ])
