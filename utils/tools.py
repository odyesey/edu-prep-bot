import re

from aiogram import Bot
from aiogram.utils.deep_linking import create_start_link
from asyncpg.protocol.record import Record

from contextlib import suppress
from datetime import datetime

from database import db
from utils.gettext import _

def validate_answers(answers: str) -> tuple[list, list]:
    answers = answers.split("\n")
    correct_answers = []
    errors = []

    for answer in answers:
        correct_answer = ".".join(answer.split(".")[1:])
        if correct_answer:
            correct_answers.append(correct_answer.strip())
        else:
            errors.append(answer)

    return correct_answers, errors

def keywords_list(keywords: str, lang: str) -> tuple[int, list[str]]:
    errors = []

    keywords = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]

    pattern = re.compile(r"^[A-Za-z0-9_'-]+$")

    if len(keywords) > 10:
        errors.append(_("keywords_limit", lang))

    if len(set(keywords)) != len(keywords):
        errors.append(_("keywords_duplicate", lang))

    for keyword in keywords:
        if not pattern.fullmatch(keyword):
            errors.append(keyword)

    if errors:
        return 0, errors

    return 1, keywords

def check_answers(answers: list[str], correct_answers: list[str]) -> list[bool]:
    answers = answers[:len(correct_answers)]
    result = []

    for answer in range(len(answers)):
        result.append(correct_answers[answer] == answers[answer])

    return result

async def delete_ended_tests(bot: Bot):
    now = datetime.now()
    tests = await db.test()

    for test in tests:
        if test['start_time'] + test['duration'] < now:
            users = await db.test_users(test['code'])
            for user in users:
                await db.set_current_test(user['user_id'], None)
                user_answers = await db.current_answers(user['user_id'])
                if user_answers:
                    msg = test['name'] + "\n"
                    result = check_answers(user_answers, test['answers'])

                    if test['rated']:
                        await db.add_rating(user['user_id'], result.count(True))

                    prev_results = await db.results(user['user_id'])
                    if not prev_results: prev_results = []
                    prev_results.append(f"{now.strftime("%d.%m.%Y")} {result.count(True)}/{len(result)}")

                    if len(prev_results) > 5:
                        prev_results.pop(0)

                    await db.update_results(user['user_id'], prev_results)

                    for answer in range(len(result)):
                        if result[answer]:
                            msg += f"\n{answer + 1}. ✅"
                        else:
                            msg += f"\n{answer + 1}. ❌"

                    await db.set_current_answers(user['user_id'], [])

                    with suppress(Exception):
                        await bot.send_message(user['user_id'], msg)

            await db.delete_test(test['code'])

def in_list(target: str, words: list[str]) -> bool:
    for word in words:
        if target.lower() == word.lower():
            return True
    return False

async def search_resources(query: str) -> list[Record]:
    matches = []
    queries = query.split()

    resources = await db.resources()
    vocabs = await db.resources(vocab=True)

    for record in resources + vocabs:
        keywords = record['keywords'] + record['title'].split()
        if record.get("description"):
            keywords += record['description'].split()

        flag = True
        for keyword in queries:
            if not in_list(keyword, keywords):
                flag = False
                break

        if flag: matches.append(record)

    return matches[:20]

async def generate_populars(bot: Bot, resources: list[Record], with_saves: bool = True, vocab_list: bool = False) -> str:
    msg = ""
    id_name = "vocabulary_id" if vocab_list else "resource_id"
    prefix = "-" if vocab_list else ""

    for resource in resources:
        link = await create_start_link(bot, prefix + str(resource[id_name]))
        msg += f"<a href=\"{link}\">{resource['title']}</a>"

        if with_saves:
            msg += f" [⭐ {resource['saves']}]"

        msg += "\n"

    return msg

def generate_vocab(text: str) -> dict | list:
    text = text.split("\n")
    result = dict()
    fails = []

    sep = "-"
    hashtag_found = False

    for num, word in enumerate(text, start=1):
        if word.count(sep) != 1:
            fails.append(word)
            continue

        if "#" in word:
            fails.append(word)
            hashtag_found = True
            continue

        if not bool(word.split(sep)[0].strip()) or not bool(word.split(sep)[1].strip()):
            fails.append(word)
            continue

        valid_word = word.split(sep)
        result[f"{valid_word[0].strip()}#{num}"] = valid_word[1].strip()

    if hashtag_found: fails.insert(0, 1)

    if fails:
        return fails
    return result
