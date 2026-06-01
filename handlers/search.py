from aiogram import Router, Bot
from aiogram.types import (InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)
from aiogram.utils.deep_linking import create_start_link

from database import db
from keyboards.inline import save_resource
from utils.tools import search_resources

router = Router()

@router.inline_query()
async def search(query: InlineQuery, bot: Bot):
    user_id = query.from_user.id
    lang = await db.lang(user_id)
    results = await search_resources(query.query)
    articles = []
    thumbnail = {
        "document": "https://emoji.aranja.com/emojis/apple/1f4c4.png",
        "video": "https://emoji.aranja.com/emojis/apple/1f4f9.png",
        "photo": "https://emoji.aranja.com/emojis/apple/1f5bc-fe0f.png",
        "vocab": "https://emoji.aranja.com/emojis/apple/1f4da.png"
    }

    for result in results:
        id_name = "vocabulary_id" if result.get("vocabulary_id") else "resource_id"
        sign = "-" if result.get("vocabulary_id") else ""

        link = await create_start_link(bot, f"{sign}{result[id_name]}")
        delete = await db.check_resource(user_id, result[id_name])
        articles.append(InlineQueryResultArticle(
            id=str(result[id_name]),
            title=result['title'],
            description=result['description'] if result.get("description") else None,
            input_message_content=InputTextMessageContent(
                message_text=f"<a href=\"{link}\">{result['title']}</a>",
            ),
            reply_markup=save_resource(lang, int(f"{sign}{result[id_name]}"), delete),
            thumbnail_url=thumbnail[result['content_type']]
            if result.get("content_type") else thumbnail['vocab'],
        ))

    await query.answer(articles, cache_time=1)