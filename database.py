import asyncpg
import json

from asyncpg import Connection
from asyncpg.pool import Pool
from asyncpg.protocol.record import Record

from datetime import datetime, timedelta
from typing import Union

from data.config import DB_USER, DB_PASS, DB_HOST, DB_NAME

class Postgres:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def create(self):
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            database=DB_NAME
        )

    async def execute(self, command, *args,
                      fetch: bool = False,
                      fetch_val: bool = False,
                      fetch_row: bool = False,
                      execute: bool = False
                      ):
        async with self.pool.acquire() as connection:
            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetch_val:
                    result = await connection.fetchval(command, *args)
                elif fetch_row:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result


class Database(Postgres):
    async def add_user(self, name: str, user_id: int, lang: str):
        sql = "INSERT INTO users (name, user_id, lang) VALUES ($1 , $2, $3)"
        await self.execute(sql, name, user_id, lang, execute=True)

    async def check_user(self, user_id: int) -> bool:
        sql = "SELECT * FROM users WHERE user_id = $1"
        result = await self.execute(sql, user_id, fetch_val=True)

        return bool(result)

    async def add_test(self,
                       rated: bool,
                       name: str,
                       file_id: str,
                       content_type: str,
                       description: str,
                       start_time: datetime,
                       duration: timedelta,
                       answers: list[str]
                       ):
        sql = ("INSERT INTO "
               "tests (rated, name, file_id, content_type, description, start_time, duration, answers)"
               "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")

        await self.execute(sql, rated,
                           name, file_id,
                           content_type, description,
                           start_time, duration,
                           answers, execute=True)

    async def leaderboard(self) -> list[Record]:
        sql = "SELECT name, rating FROM users ORDER BY rating DESC LIMIT 20"
        return await self.execute(sql, fetch=True)

    async def get_rating(self, user_id: int) -> int:
        sql = "SELECT rating FROM users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch_val=True)
    
    async def add_resource(self,
                           user_id: int,
                           title: str,
                           file_id: str,
                           content_type: str,
                           description: str,
                           keywords: list[str],
                           ):
        sql = ("INSERT INTO "
               "resources (user_id, title, file_id, content_type, description, keywords)"
               "VALUES ($1, $2, $3, $4, $5, $6)")
        await self.execute(sql, user_id,
                           title, file_id,
                           content_type, description,
                           keywords, execute=True)

    async def popular_resources(self) -> list[Record]:
        sql = "SELECT * FROM resources ORDER BY saves DESC LIMIT 10"
        return await self.execute(sql, fetch=True)

    async def saved_resources(self, user_id: int) -> list[Record]:
        sql = f"SELECT saved_resources FROM users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch_val=True)

    async def resources(self, resource_id: int | None = None, vocab: bool = False) -> list[Record]:
        table = "vocabulary " if vocab else "resources"
        column = "vocabulary_id" if vocab else "resource_id"
        resource_id = abs(resource_id) if resource_id else None

        if resource_id:
            sql = f"SELECT * FROM {table} WHERE {column} = $1"
            return await self.execute(sql, resource_id, fetch_row=True)

        sql = f"SELECT * FROM {table}"
        return await self.execute(sql, fetch=True)

    async def save_resource(self, user_id: int, resource_id: str, delete: bool = False):
        sql = """UPDATE users
                 SET saved_resources = array_append(
                     COALESCE(saved_resources, '{}'),
                     $2
                     )
                     WHERE user_id = $1
                     AND NOT ($2 = ANY(COALESCE(saved_resources, '{}')))"""

        if delete:
            sql = "UPDATE users SET saved_resources = array_remove(saved_resources, $2) WHERE user_id = $1"
        return await self.execute(sql, user_id, resource_id, execute=True)

    async def add_resource_saves(self, resource_id: int, subtract: bool = False):
        sql = "UPDATE resources SET saves = saves + 1 WHERE resource_id = $1"
        if subtract:
            sql = "UPDATE resources SET saves = saves - 1 WHERE resource_id = $1"
        await self.execute(sql, resource_id, execute=True)

    async def check_resource(self, user_id: int, resource_id: str) -> bool:
        sql = "SELECT * FROM users WHERE user_id = $1 AND $2 = ANY(saved_resources)"
        result = await self.execute(sql, user_id, resource_id, fetch_val=True)

        return bool(result)

    async def add_vocab(self,
                             user_id: int,
                             title: str,
                             words: dict,
                             keywords: list[str]
                             ):
        sql = ("INSERT INTO vocabulary"
               "(user_id, title, words, keywords) "
               "VALUES ($1, $2, $3, $4)")
        await self.execute(sql, user_id, title, json.dumps(words), keywords, execute=True)

    async def popular_vocabs(self) -> list[Record]:
        sql = "SELECT * FROM vocabulary ORDER BY saves DESC LIMIT 10"
        return await self.execute(sql, fetch=True)

    async def update_current_vocab(self, user_id: int, vocab_data: dict):
        sql = "UPDATE users SET current_vocabulary = $2 WHERE user_id = $1"
        await self.execute(sql, user_id, json.dumps(vocab_data), execute=True)

    async def check_current_vocab(self, user_id: int, vocab_id: int) -> bool:
        sql = "SELECT current_vocabulary FROM users WHERE user_id = $1"
        result = json.loads(await self.execute(sql, user_id, fetch_val=True))

        if not result or result['vocabulary_id'] != vocab_id:
            return False
        return True

    async def current_vocab(self, user_id: int) -> dict:
        sql = "SELECT current_vocabulary FROM users WHERE user_id = $1"
        return json.loads(await self.execute(sql, user_id, fetch_val=True))

    async def word(self, vocab_id: int, word_id: int) -> tuple | None:
        sql = "SELECT words FROM vocabulary WHERE vocabulary_id = $1"
        result = json.loads(await self.execute(sql, vocab_id, fetch_val=True))

        for key, val in result.items():
            if f"#{word_id}" in key:
                return key.split("#")[0], val, int(key.split("#")[1])
        return None

    async def change_lang(self, user_id: int, lang: str):
        sql = "UPDATE users SET lang = $2 WHERE user_id = $1"
        await self.execute(sql, user_id, lang, execute=True)

    async def lang(self, user_id: int) -> str:
        sql = "SELECT lang FROM users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch_val=True)

    async def verify(self, user_id: int):
        sql = "UPDATE users SET verified = $1 WHERE user_id = $2"
        await self.execute(sql, True, user_id, execute=True)

    async def is_verified(self, user_id: int) -> bool:
        sql = "SELECT verified FROM users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch_val=True)

db = Database()
