from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database import db
from keyboards.reply import cancel_button, vocabulary_keyboard
from utils.filters import Text
from utils.gettext import _
from utils.states import AddVocabulary
from utils.tools import generate_vocab, keywords_list

router = Router()

@router.message(Text("vocabulary"))
async def vocabulary(message: Message):
    lang = await db.lang(message.from_user.id)
    await message.answer("popular_vocabularies", reply_markup=vocabulary_keyboard(lang))


@router.message(Text("vocabulary_add"))
async def add_vocabulary(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    await state.set_state(AddVocabulary.title)
    await message.answer(_("vocabulary_title", lang),
                                  reply_markup=cancel_button(lang))


@router.message(AddVocabulary.title, F.text)
async def title(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    if len(message.text) <= 50:
        await state.update_data(title=message.text)
        await state.set_state(AddVocabulary.words)
        await message.answer(_("vocabulary_words", lang))
    else:
        await message.answer(_("vocabulary_title_limit", lang).format(
            title_len=len(message.text)
        ))


@router.message(AddVocabulary.words, F.text)
async def separator(message: Message, state: FSMContext):
    lang = await db.lang(message.from_user.id)
    vocab = generate_vocab(message.text)

    if isinstance(vocab, dict):
        await state.update_data(words=vocab)
        await state.set_state(AddVocabulary.keywords)
        await message.answer(_("keywords", lang))
    else:
        msg = _("vocabulary_words_error", lang)

        start = 0
        if isinstance(vocab[0], int):
            msg += "\n" + _("vocabulary_hashtag_detected", lang)
            start = 1

        for fail in range(start, len(vocab)):
            msg += "\n" + vocab[fail]

        await message.answer(msg)


@router.message(AddVocabulary.keywords, F.text)
async def check_keywords(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    status_code, keywords = keywords_list(message.text, lang)

    if status_code:
        data = await state.get_data()
        await db.add_vocabulary(
            user_id=user_id,
            title=data['title'],
            words=data['words'],
            keywords=keywords
        )
        await state.clear()
        await message.answer(_("vocabulary_added", lang),
                             reply_markup=vocabulary_keyboard(lang))
    else:
        error_msg = _("keywords_error", lang) + "\n"
        error_msg += "\n".join(keywords)
        await message.answer(error_msg)


@router.message(StateFilter(AddVocabulary), ~F.text)
async def invalid_format(message: Message):
    lang = await db.lang(message.from_user.id)
    await message.answer(_("invalid_format", lang))
