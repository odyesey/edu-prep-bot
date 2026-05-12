from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database import db
from keyboards.inline import verify_button
from keyboards.reply import start_keyboard, channels_list
from utils.gettext import _
from utils.states import Verify

router = Router()

@router.message(Command("verify"))
async def verify(message: Message):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    if await db.is_verified(user_id):
        await message.answer(_("already_verified", lang))
    else:
        await message.answer(_("verify_requirements", lang),
                             reply_markup=verify_button(lang))


@router.callback_query(F.data == "verify")
async def start_verify(callback: CallbackQuery, state: FSMContext):
    lang = await db.lang(callback.from_user.id)

    await state.set_state(Verify.channel)
    await callback.message.delete()
    await callback.message.answer(_("send_channel_data", lang),
                                  reply_markup=channels_list(lang))

@router.message(StateFilter(Verify.channel), F.chat_shared)
async def check_channel(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    lang = await db.lang(user_id)
    channel_id = message.chat_shared.chat_id

    try:
        bot_role = await bot.get_chat_member(channel_id, bot.id)
        if not bot_role.status in {"creator", "administrator"}:
            raise Exception
    except Exception:
        await message.answer(_("bot_not_admin", lang))
        return

    try:
        user_role = await bot.get_chat_member(channel_id, user_id)
        if not user_role.status in {"creator", "administrator"}:
            raise Exception
    except Exception:
        await message.answer(_("user_not_admin", lang))
        return

    members = await bot.get_chat_member_count(channel_id)

    if members >= 20_000:
        await db.verify(user_id)
        await message.answer(_("user_verified", lang),
                             reply_markup=start_keyboard(lang))
        await state.clear()
    else:
        await message.answer(_("not_enough_members", lang))

