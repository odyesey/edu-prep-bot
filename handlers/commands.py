from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards.inline import auto_detected_lang, lang_menu
from keyboards.reply import start_keyboard, tests_keyboard
from utils.filters import Text
from utils.gettext import locales, _

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id

    if not await db.check_user(user_id):
        lang = message.from_user.language_code

        if lang in locales:
            await message.answer(_("lang_detected", lang),
                                 reply_markup=auto_detected_lang(lang))
        else:
            await message.answer("💬?", reply_markup=lang_menu())

    else:
        lang = await db.lang(user_id)
        await message.answer(_("start", lang), reply_markup=start_keyboard(lang))


@router.callback_query(F.data.startswith("lang"))
async def set_lang(callback: CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data.split("_")[1]

    if data == "menu":
        await callback.message.edit_text(_("select_other_lang", data),
                                         reply_markup=lang_menu())
    else:
        if await db.check_user(user_id):
            await db.change_lang(user_id, data)
            await callback.message.delete()
            await callback.message.answer(_("lang_changed", data),
                                             reply_markup=start_keyboard(data))
        else:
            await db.add_user(callback.from_user.full_name, user_id, data)
            await callback.message.delete()
            await callback.message.answer(_("welcome", data).format(
                first_name=callback.from_user.first_name
            ), reply_markup=start_keyboard(data))


@router.message(Text("back"))
async def back(message: Message):
    lang = await db.lang(message.from_user.id)
    await message.answer(_("main_menu", lang), reply_markup=start_keyboard(lang))


@router.message(Text("cancel"))
@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    await state.clear()
    await message.answer(_("canceled", lang),
                         reply_markup=start_keyboard(lang))
