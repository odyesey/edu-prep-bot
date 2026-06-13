import json

from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database import db
from keyboards.inline import vocab_button, vocab_learning_keyboard, yes_no
from keyboards.reply import cancel_button, vocabulary_keyboard
from utils.filters import PositiveId, Text
from utils.gettext import _
from utils.states import AddVocabulary
from utils.tools import generate_populars, generate_vocab, keywords_list

router = Router()

@router.message(Text("vocabulary"))
async def vocabulary(message: Message, bot: Bot):
    lang = await db.lang(message.from_user.id)
    popular_vocabs = await db.popular_vocabs()
    msg = _("popular_vocabularies", lang) + "\n"
    msg += await generate_populars(bot, popular_vocabs, vocab_list=True)
    await message.answer(msg, reply_markup=vocabulary_keyboard(lang))


@router.message(CommandStart(deep_link=True), ~PositiveId())
async def send_vocab(message: Message, command: CommandObject):
    user_id = message.from_user.id
    lang = await db.lang(user_id)
    payload = command.args

    try:
        vocab = await db.resources(int(payload), vocab=True)
        continue_ = await db.check_current_vocab(user_id, int(vocab['vocabulary_id']))
        if vocab:
            await message.answer(vocab['title'],
                                 reply_markup=vocab_button(lang,
                                                           int(vocab['vocabulary_id']),
                                                           continue_))
        else:
            await message.answer(_("vocabulary_not_found", lang))
    except ValueError:
        await message.answer(_("vocabulary_not_found", lang))


@router.callback_query(F.data.startswith("vocab"))
async def process_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)
    vocab_id = int(callback.data.split("_")[1])
    current_vocab = await db.check_current_vocab(user_id, vocab_id)
    if current_vocab:
        vocab = await db.current_vocab(user_id)
        words = json.loads((await db.resources(vocab['vocabulary_id'], vocab=True))['words'])


        if len(vocab['words']) >= len(words):
            return await callback.message.edit_text(_("vocabulary_learn_completed", lang),
                                                    reply_markup=vocab_learning_keyboard(lang, finished=True))

        for word_id in range(1, len(words) + 1):
            if not word_id in vocab['words']:
                break

        vocab['last_word'] = word_id
        await db.update_current_vocab(user_id, vocab)

        word = await db.word(vocab['vocabulary_id'], word_id)
        await callback.message.edit_text(f"{word[0]}\n\n<tg-spoiler>{word[1]}</tg-spoiler>",
                                         reply_markup=vocab_learning_keyboard(lang))
    else:
        await callback.message.edit_text(_("vocabulary_reset_confirm", lang),
                                         reply_markup=yes_no(lang, f"begin_{vocab_id}_"))


@router.callback_query(F.data.startswith("begin"))
async def start_vocab(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)
    data = callback.data.split("_")
    vocab_id = int(data[1])
    decision = data[2]

    if decision == "yes":
        vocab_data = {
            "vocabulary_id": vocab_id,
            "reverse": False,
            "last_word": 1,
            "words": []
        }
        await db.update_current_vocab(user_id, vocab_data)
        word = await db.word(vocab_id, 1)
        await callback.message.edit_text(f"{word[0]}\n\n<tg-spoiler>{word[1]}</tg-spoiler>",
                                         reply_markup=vocab_learning_keyboard(lang))
    else:
        vocab = await db.resources(vocab_id, vocab=True)
        continue_ = await db.check_current_vocab(user_id, int(vocab['vocabulary_id']))
        await callback.message.edit_text(vocab['title'],
                                         reply_markup=vocab_button(lang,
                                                                   int(vocab['vocabulary_id']),
                                                                   continue_))


@router.callback_query(F.data.startswith("word"))
async def process_word(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await db.lang(user_id)
    correct = int(callback.data.split("_")[1])
    vocab = await db.current_vocab(user_id)
    words = json.loads((await db.resources(vocab['vocabulary_id'], vocab=True))['words'])

    if correct == 0:
        vocab['last_word'] = 0
        if len(vocab['words']) >= len(words):
            vocab['words'] = []

    if correct > 0:
        vocab['words'].append(vocab['last_word'])

    word_id = vocab['last_word']
    cycle_finished = False
    while True:
        word_id += 1
        if word_id > len(words):
            cycle_finished = True
            break
        if word_id not in vocab['words']:
            break

    if cycle_finished:
        text = _("vocabulary_learn_finished", lang)
        if len(vocab['words']) >= len(words):
            text = _("vocabulary_learn_completed", lang)

        await callback.message.edit_text(text, reply_markup=vocab_learning_keyboard(lang, finished=True))
    else:
        vocab['last_word'] = word_id

        word = await db.word(vocab['vocabulary_id'], word_id)
        try:
            await callback.message.edit_text(f"{word[0]}\n\n<tg-spoiler>{word[1]}</tg-spoiler>",
                                             reply_markup=vocab_learning_keyboard(lang))
        except TelegramBadRequest:
            await callback.answer()

    await db.update_current_vocab(user_id, vocab)


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
        await db.add_vocab(
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


@router.message(Text("continue"))
async def continue_vocab(message: Message):
    user_id = message.from_user.id
    lang = await db.lang(user_id)

    vocab = await db.current_vocab(user_id)
    if vocab:
        words = json.loads((await db.resources(vocab['vocabulary_id'], vocab=True))['words'])

        if len(vocab['words']) >= len(words):
            return await message.answer(_("vocabulary_learn_completed", lang),
                                        reply_markup=vocab_learning_keyboard(lang, finished=True))

        for word_id in range(1, len(words) + 1):
            if not word_id in vocab['words']:
                break

        vocab['last_word'] = word_id
        await db.update_current_vocab(user_id, vocab)

        word = await db.word(vocab['vocabulary_id'], word_id)
        await message.answer(f"{word[0]}\n\n<tg-spoiler>{word[1]}</tg-spoiler>",
                                         reply_markup=vocab_learning_keyboard(lang))
    else:
        await message.answer(_("vocabulary_not_found", lang))
