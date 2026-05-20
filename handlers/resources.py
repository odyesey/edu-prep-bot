from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (Message, CallbackQuery,
                           InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)
from aiogram.utils.deep_linking import create_start_link

from database import db
from keyboards.inline import resources_keyboard, save_resource, yes_no
from keyboards.reply import cancel_button, start_keyboard
from utils.filters import Text
from utils.gettext import _
from utils.states import AddResource
from utils.tools import keywords_list, search_resources

router = Router()

@router.message(Text("resources"))
async def resources(message: Message):
    lang = await db.lang(message.from_user.id)
    await message.answer(_("resources", lang),
                         reply_markup=resources_keyboard(lang))


@router.inline_query()
async def search(query: InlineQuery, bot: Bot):
    user_id = query.from_user.id
    lang = await db.lang(user_id)
    results = await search_resources(query.query)
    articles = []
    await db.save_resource(user_id, 4)
    thumbnail = {
        "document": "https://emoji.aranja.com/emojis/apple/1f4c4.png",
        "video": "https://emoji.aranja.com/emojis/apple/1f4f9.png",
        "photo": "https://emoji.aranja.com/emojis/apple/1f5bc-fe0f.png",
    }

    for result in results:
        link = await create_start_link(bot, result['resource_id'])
        delete = await db.check_resource(user_id, result['resource_id'])
        articles.append(InlineQueryResultArticle(
            id=str(result['resource_id']),
            title=result['title'],
            description=result['description'],
            input_message_content=InputTextMessageContent(
                message_text=f"<a href=\"{link}\">{result['title']}</a>",
            ),
            reply_markup=save_resource(lang, result['resource_id'], delete),
            thumbnail_url=thumbnail[result['content_type']],
        ))

    await query.answer(articles, cache_time=1)


@router.message(CommandStart(deep_link=True))
async def send_resource(message: Message, command: CommandObject):
    lang = await db.lang(message.from_user.id)
    payload = command.args

    if payload.isdigit():
        resource = await db.resources(int(payload))
        if resource:
            if resource['content_type'] == 'document':
                await message.answer_document(resource['file_id'], caption=resource['description'])
            elif resource['content_type'] == 'video':
                await message.answer_video(resource['file_id'], caption=resource['description'])
            elif resource['content_type'] == 'photo':
                await message.answer_photo(resource['file_id'], caption=resource['description'])
        else:
            await message.answer(_("resource_not_found", lang))
    else:
        await message.answer(_("resource_not_found", lang))


@router.callback_query(F.data.startswith("save"))
async def save_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)
    data = callback.data.split("_")
    mode = bool(int(data[1]))
    resource_id = int(data[2])

    await db.save_resource(user_id, resource_id, mode)
    await bot.edit_message_reply_markup(inline_message_id=callback.inline_message_id,
                                        reply_markup=save_resource(lang, resource_id, not mode))
    if mode:
        await callback.answer(_("deleted", lang))
    else:
        await callback.answer(_("saved", lang))


@router.callback_query(F.data == "resources_add")
async def add_resource(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)

    await state.set_state(AddResource.title)
    await callback.answer()
    await callback.message.answer(_("resource_title", lang),
                                  reply_markup=cancel_button(lang))


@router.message(AddResource.title, F.text)
async def title(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    await state.update_data(title=message.text)
    await state.set_state(AddResource.file)
    await message.answer(_("resource_file", lang))


@router.message(AddResource.file, (F.document | F.video | F.photo))
async def file(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    if message.document: content_type = "document"; file_id = message.document.file_id
    elif message.video: content_type = "video"; file_id = message.video.file_id
    elif message.photo: content_type = "photo"; file_id = message.photo[-1].file_id

    await state.update_data(file_id=file_id, content_type=content_type)
    await state.set_state(AddResource.description)

    if message.caption:
        if len(message.caption) <= 1024:
            await state.update_data(description=message.caption)
            await message.answer(_("resource_use_caption", lang),
                                 reply_markup=yes_no(lang, "description_"))
        else:
            await message.answer(_("resource_caption_limit", lang))
    else:
        await message.answer(_("resource_description", lang))


@router.message(AddResource.description, F.text)
async def description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)
    desc_len = len(message.text)

    if desc_len <= 1024:
        await state.update_data(description=message.text)
        await state.set_state(AddResource.keywords)
        await message.answer(_("resource_keywords", lang))
    else:
        await message.answer(_("description_limit", lang).format(
            desc_len=desc_len
        ))


@router.callback_query(AddResource.description, F.data.startswith("description"))
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    lang = await db.lang(callback.from_user.id)
    decision = callback.data.split("_")[1]

    await callback.message.delete()

    if decision == "yes":
        await state.set_state(AddResource.keywords)
        await callback.message.answer(_("resource_keywords", lang))
    else:
        await callback.message.answer(_("resource_description", lang))


@router.message(AddResource.keywords, F.text)
async def check_keywords(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    status_code, keywords = keywords_list(message.text, lang)

    if status_code:
        data = await state.get_data()
        await db.add_resource(
            user_id=user_id,
            title=data['title'],
            file_id=data['file_id'],
            content_type=data['content_type'],
            description=data['description'],
            keywords=keywords
        )
        await state.clear()
        await message.answer(_("resource_added", lang),
                             reply_markup=start_keyboard(lang))
    else:
        error_msg = _("resource_keywords_error", lang) + "\n"
        error_msg += "\n".join(keywords)
        await message.answer(error_msg)


@router.message(StateFilter(AddResource.title, AddResource.description), ~F.text)
@router.message(AddResource.file, ~(F.document | F.video | F.photo))
async def invalid_format(message: Message):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    await message.answer(_("invalid_format", lang))
