from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from contextlib import suppress
from datetime import datetime, timedelta
from random import randint

from database import db
from keyboards.inline import active_test_keyboard, yes_no
from keyboards.reply import tests_keyboard, cancel_button
from utils.tools import validate_answers
from utils.filters import Text
from utils.gettext import _
from utils.states import HostTest, JoinTest

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

        while True:
            code = randint(1000, 9999)

            if await db.check_code(code):
                break

        await db.add_test(rated=data['rated'],
                          name=data['name'],
                          file_id=data['file_id'],
                          content_type=data['content_type'],
                          description=data['description'],
                          start_time=data['time'],
                          duration=data['duration'],
                          answers=result[0],
                          code=code)

        await message.answer(_("test_added", lang).format(code=f"<code>{code}</code>"),
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


@router.message(Text("join_test"))
async def join_test(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)

    await state.set_state(JoinTest.code)
    await message.answer(_("test_enter_code", lang), reply_markup=cancel_button(lang))


@router.message(JoinTest.code, F.text)
async def check_code(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)
    try:
        code = int(message.text)
        if not await db.check_code(code):
            test = await db.test(code)
            now = datetime.now()

            if test['start_time'] <= now < test['start_time'] + test['duration']:
                await db.set_current_test(user_id, code)
                await state.clear()
                total_seconds = (test['start_time'] + test['duration'] - now).total_seconds()
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                kwargs = {
                    "caption": f"🕑 {round(hours)}:{round(minutes)}"
                               f"\n{test['name']}\n\n{test['description']}",
                    "reply_markup": active_test_keyboard(lang)
                }

                await message.answer(_("test_found", lang), reply_markup=tests_keyboard(lang))
                if test['content_type'] == "document":
                    await message.answer_document(test['file_id'], **kwargs)
                elif test['content_type'] == "photo":
                    await message.answer_photo(test['file_id'], **kwargs)

            elif now > test['start_time'] + test['duration']:
                await message.answer(_("test_late", lang))
            elif now < test['start_time']:
                await message.answer(_("test_early", lang))
        else:
            await message.answer(_("test_not_found", lang))
    except ValueError:
        await message.answer(_("test_not_found", lang))


@router.callback_query(F.data == "submit")
async def submit_answers(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    user_id = callback.from_user.id
    lang = await db.lang(user_id)

    test = await db.current_test(user_id)

    if test:
        await state.set_state(JoinTest.submit)
        await callback.message.answer(_("enter_test_answers", lang),
                                      reply_markup=cancel_button(lang))
    else:
        await callback.answer(_("test_not_found", lang))

    await state.set_state(JoinTest.submit)


@router.message(JoinTest.submit, F.text)
async def process_answers(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    result = validate_answers(message.text)

    if result[1]:
        result[1].insert(0, _("invalid_test_answers", lang))
        await message.answer("\n".join(result[1]))
    else:
        await state.clear()
        await db.set_current_answers(user_id, result[0])
        await message.answer(_("test_answers_received", lang),
                             reply_markup=tests_keyboard(lang))


@router.callback_query(F.data == "refresh")
async def refresh_test(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)
    code = await db.current_test(user_id)

    if code:
        test = await db.test(code)
        now = datetime.now()

        total_seconds = (test['start_time'] + test['duration'] - now).total_seconds()
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        caption = (f"🕑 {round(hours)}:{round(minutes)}"
                   f"\n{test['name']}\n\n{test['description']}")

        with suppress(Exception):
            await callback.message.edit_caption(caption=caption,
                                                reply_markup=active_test_keyboard(lang))
        await callback.answer()
    else:
        await callback.answer(_("test_late", lang))


@router.message(Text("previous_results"))
async def last_results(message: Message):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    msg = _("previous_results", lang) + "\n"
    results = await db.results(user_id)

    if results:
        for result in range(len(results) - 1, -1, -1):
            msg += results[result] + "\n"

    await message.answer(msg)
