from __future__ import annotations

from typing import Optional

import aiosqlite

from config import GuildConfig, DEFAULT_MESSAGE


class Database:
    def __init__(self, path: str = "bot.db") -> None:
        self.path = path
        self.conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS guild_config(
            guild_id INTEGER PRIMARY KEY,
            staff_role_id INTEGER,
            reminder_message TEXT,
            schedule_cron TEXT,
            last_sent_at TEXT,
            log_channel_id INTEGER
        )"""
        )
        async with self.conn.execute("PRAGMA table_info(guild_config)") as cur:
            cols = [row[1] for row in await cur.fetchall()]
        if "log_channel_id" not in cols:
            await self.conn.execute(
                "ALTER TABLE guild_config ADD COLUMN log_channel_id INTEGER"
            )
        await self.conn.execute(
            """CREATE TABLE IF NOT EXISTS send_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER,
            user_id INTEGER,
            status TEXT CHECK(status IN ('sent','failed')),
            error TEXT,
            sent_at TEXT
        )"""
        )
        await self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_send_log_guild_status ON send_log(guild_id, status)"
        )
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def get_guild_config(self, guild_id: int) -> GuildConfig:
        assert self.conn is not None
        async with self.conn.execute(
            "SELECT staff_role_id, reminder_message, schedule_cron, last_sent_at, log_channel_id FROM guild_config WHERE guild_id=?",
            (guild_id,),
        ) as cur:
            row = await cur.fetchone()
        if row:
            return GuildConfig(
                guild_id=guild_id,
                staff_role_id=row[0],
                reminder_message=row[1] or DEFAULT_MESSAGE,
                schedule_cron=row[2],
                last_sent_at=row[3],
                log_channel_id=row[4],
            )
        cfg = GuildConfig(guild_id=guild_id)
        await self.upsert_guild_config(cfg)
        return cfg

    async def upsert_guild_config(self, cfg: GuildConfig) -> None:
        assert self.conn is not None
        await self.conn.execute(
            """INSERT INTO guild_config(guild_id, staff_role_id, reminder_message, schedule_cron, last_sent_at, log_channel_id)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(guild_id) DO UPDATE SET
                staff_role_id=excluded.staff_role_id,
                reminder_message=excluded.reminder_message,
                schedule_cron=excluded.schedule_cron,
                last_sent_at=excluded.last_sent_at,
                log_channel_id=excluded.log_channel_id
            """,
            (
                cfg.guild_id,
                cfg.staff_role_id,
                cfg.reminder_message,
                cfg.schedule_cron,
                cfg.last_sent_at,
                cfg.log_channel_id,
            ),
        )
        await self.conn.commit()

    async def update_guild_config(self, guild_id: int, **fields) -> GuildConfig:
        cfg = await self.get_guild_config(guild_id)
        for k, v in fields.items():
            setattr(cfg, k, v)
        await self.upsert_guild_config(cfg)
        return cfg

    async def log_send(self, guild_id: int, user_id: int, status: str, error: Optional[str]) -> None:
        assert self.conn is not None
        await self.conn.execute(
            "INSERT INTO send_log(guild_id, user_id, status, error, sent_at) VALUES (?,?,?,?,datetime('now'))",
            (guild_id, user_id, status, error),
        )
        await self.conn.commit()
