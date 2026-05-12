import asyncpg

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
    async def add_user(self, name: str, user_id: int, lang: str) -> None:
        sql = "INSERT INTO users (name, user_id, lang) VALUES ($1 , $2, $3)"
        await self.execute(sql, name, user_id, lang, execute=True)

    async def check_user(self, user_id: int) -> bool:
        sql = "SELECT * FROM users WHERE user_id = $1"
        result = await self.execute(sql, user_id, fetch_val=True)

        return bool(result)

    async def add_test(self,
                       name: str,
                       file_id: str,
                       content_type: str,
                       description: str,
                       start_time: datetime,
                       duration: timedelta,
                       answers: list[str]
                       ) -> None:
        sql = ("INSERT INTO "
               "tests (rated, name, file_id, content_type, description, start_time, duration, answers)"
               "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)")

        await self.execute(sql, False,
                           name, file_id,
                           content_type, description,
                           start_time, duration,
                           answers, execute=True)

    async def leaderboard(self) -> list[Record]:
        sql = "SELECT name, rating FROM users ORDER BY RATING DESC LIMIT 20"
        return await self.execute(sql, fetch=True)

    async def get_rating(self, user_id: int) -> int:
        sql = "SELECT rating FROM users WHERE user_id = $1"
        return await self.execute(sql, user_id, fetch_val=True)

    async def change_lang(self, user_id: int, lang: str) -> None:
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
