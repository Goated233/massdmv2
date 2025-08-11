from __future__ import annotations

from datetime import datetime, UTC
from typing import Dict

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import GuildConfig


class Scheduler:
    def __init__(self, bot, db, dm_queue) -> None:
        self.bot = bot
        self.db = db
        self.dm_queue = dm_queue
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[int, str] = {}

    def start(self) -> None:
        self.scheduler.start()

    def schedule_guild(self, guild_id: int, cfg: GuildConfig) -> None:
        if not cfg.schedule_cron:
            return
        self.cancel_guild(guild_id)
        trigger = CronTrigger.from_crontab(cfg.schedule_cron)
        job = self.scheduler.add_job(self._run_job, trigger, args=[guild_id])
        self.jobs[guild_id] = job.id

    def cancel_guild(self, guild_id: int) -> None:
        job_id = self.jobs.pop(guild_id, None)
        if job_id:
            self.scheduler.remove_job(job_id)

    async def _run_job(self, guild_id: int) -> None:
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return
        cfg = await self.db.get_guild_config(guild_id)
        await self.dm_queue.send(guild, cfg)
        await self.db.update_guild_config(
            guild_id, last_sent_at=datetime.now(UTC).isoformat()
        )
