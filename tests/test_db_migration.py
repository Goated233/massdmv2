import asyncio
import aiosqlite

from db import Database


def test_connect_adds_log_channel(tmp_path):
    db_path = tmp_path / "test.db"

    async def setup_old_schema():
        conn = await aiosqlite.connect(db_path)
        await conn.execute(
            """CREATE TABLE guild_config(
            guild_id INTEGER PRIMARY KEY,
            staff_role_id INTEGER,
            reminder_message TEXT,
            schedule_cron TEXT,
            last_sent_at TEXT
        )"""
        )
        await conn.commit()
        await conn.close()

    asyncio.run(setup_old_schema())

    db = Database(str(db_path))
    asyncio.run(db.connect())

    async def fetch_columns():
        assert db.conn is not None
        async with db.conn.execute("PRAGMA table_info(guild_config)") as cur:
            return [row[1] for row in await cur.fetchall()]

    cols = asyncio.run(fetch_columns())
    assert "log_channel_id" in cols
    asyncio.run(db.close())
