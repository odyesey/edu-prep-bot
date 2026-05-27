from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from datetime import datetime, timedelta

from database import db
from keyboards.inline import yes_no
from keyboards.reply import tests_keyboard, cancel_button
from utils.tools import validate_answers
from utils.filters import Text
from utils.gettext import _
from utils.states import HostTest

router = Router()

@router.message(Text("tests"))
async def tests(message: Message):
    lang = await db.lang(message.from_user.id)
    await message.answer(_("tests_menu", lang), reply_markup=tests_keyboard(lang))


@router.message(Text("host_test"))
async def host_test(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    await state.update_data(rated=False)

    if await db.is_verified(user_id):
        await state.set_state(HostTest.rated)
        await message.answer(_("test_rated", lang), reply_markup=yes_no(lang, "rated_"))
    else:
        await state.set_state(HostTest.name)
        await message.answer(_("not_rated_test_name", lang), reply_markup=cancel_button(lang))


@router.callback_query(F.data.startswith("rated"))
async def test_name(callback: CallbackQuery, state: FSMContext):
    lang = await db.lang(callback.from_user.id)
    status = callback.data.split("_")[1]

    if status == "yes":
        await state.update_data(rated=True)

    await state.set_state(HostTest.name)
    await callback.message.delete()
    await callback.message.answer(_("test_name", lang), reply_markup=cancel_button(lang))


@router.message(HostTest.name, F.text)
async def set_name(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    await state.update_data(name=message.text)
    await state.set_state(HostTest.file)

    await message.answer(_("send_test_file", lang))


@router.message(HostTest.file, F.photo | F.document)
async def test_file(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    if message.document:
        await state.update_data(file_id=message.document.file_id,
                                content_type="document")
    if message.photo:
        await state.update_data(file_id=message.photo[-1].file_id,
                                content_type="photo")

    await state.set_state(HostTest.description)

    if message.caption:
        if len(message.caption) <= 1024:
            await state.update_data(description=message.caption)
            await message.answer(_("test_description_detected", lang),
                                 reply_markup=yes_no(lang, "description_"))
        else:
            await message.answer(_("test_caption_limit", lang))
    else:
        await message.answer(_("enter_test_description", lang))


@router.message(HostTest.description, F.text)
async def test_description(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)
    desc_len = len(message.text)

    if desc_len <= 1024:
        await state.update_data(description=message.text)
        await state.set_state(HostTest.time)
        await message.answer(_("enter_test_timestamp", lang))
    else:
        await message.answer(_("description_limit", lang).format(
            desc_len=desc_len
        ))


@router.callback_query(HostTest.description, F.data.startswith("description"))
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    lang = await db.lang(callback.from_user.id)
    decision = callback.data.split("_")[1]

    await callback.message.delete()

    if decision == "yes":
        await state.set_state(HostTest.time)
        await callback.message.answer(_("enter_test_timestamp", lang))
    else:
        await callback.message.answer(_("enter_test_description", lang))


@router.message(HostTest.time, F.text)
async def check_timestamp(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    try:
        time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        if time < datetime.now():
            await message.answer(_("invalid_test_time", lang))
            return
    except ValueError:
        await message.answer(_("invalid_format", lang))
        return

    await state.update_data(time=time)
    await state.set_state(HostTest.duration)
    await message.answer(_("enter_test_duration", lang))


@router.message(HostTest.duration, F.text)
async def check_duration(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    try:
        hours, minutes = map(int, message.text.split(":"))
        duration = timedelta(hours=hours, minutes=minutes)
        if duration > timedelta(hours=48):
            await message.answer(_("invalid_test_duration", lang))
            return
    except ValueError:
        await message.answer(_("invalid_format", lang))
        return

    await state.update_data(duration=duration)
    await state.set_state(HostTest.answers)
    await message.answer(_("enter_test_answers", lang))


@router.message(HostTest.answers, F.text)
async def check_answers(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)
    result = validate_answers(message.text)

    if result[1]:
        result[1].insert(0, _("invalid_test_answers", lang))
        await message.answer("\n".join(result[1]))
    else:
        data = await state.get_data()

        await db.add_test(rated=data['rated'],
                          name=data['name'],
                          file_id=data['file_id'],
                          content_type=data['content_type'],
                          description=data['description'],
                          start_time=data['time'],
                          duration=data['duration'],
                          answers=result[0])

        await message.answer(_("test_added", lang),
                             reply_markup=tests_keyboard(lang))
        await state.clear()


@router.message(HostTest.file, ~F.document)
@router.message(StateFilter(HostTest.name, HostTest.description,
                            HostTest.time, HostTest.duration,
                            HostTest.answers), ~F.text)
async def invalid(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)
    current_state = await state.get_state()

    if current_state == HostTest.name:
        await message.answer(_("invalid_test_name", lang))
    elif current_state == HostTest.description:
        await message.answer(_("invalid_test_description", lang))
    else:
        await message.answer(_("invalid_format", lang))
