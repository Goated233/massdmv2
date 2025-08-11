from __future__ import annotations

import asyncio
import time
from typing import Callable, Iterable, Tuple

import discord

from config import GuildConfig, render_message
from embeds import build_reminder_embed


class RateLimiter:
    def __init__(self, min_interval: float, time_func: Callable[[], float] = time.monotonic) -> None:
        self.min_interval = min_interval
        self.time_func = time_func
        self._last: float | None = None

    async def wait(self) -> None:
        now = self.time_func()
        if self._last is not None:
            delta = now - self._last
            if delta < self.min_interval:
                await asyncio.sleep(self.min_interval - delta)
        self._last = self.time_func()


class DMQueue:
    def __init__(self, db, rate_limiter: RateLimiter | None = None) -> None:
        self.db = db
        self.rate_limiter = rate_limiter or RateLimiter(2.0)

    async def send(self, guild: discord.Guild, cfg: GuildConfig) -> Tuple[int, int, int, float]:
        role = guild.get_role(cfg.staff_role_id) if cfg.staff_role_id else None
        if not role:
            return 0, 0, 0, 0.0
        members = [m for m in role.members if not m.bot]
        total = len(members)
        sent = failed = 0
        for member in members:
            await self.rate_limiter.wait()
            msg = render_message(cfg.reminder_message, guild.name, member.display_name)
            embed = build_reminder_embed(guild.name, msg)
            try:
                await member.send(embed=embed)
                await self.db.log_send(guild.id, member.id, "sent", None)
                sent += 1
            except discord.HTTPException as e:
                if e.status == 429 and getattr(e, "retry_after", None):
                    await asyncio.sleep(e.retry_after)
                    try:
                        await member.send(embed=embed)
                        await self.db.log_send(guild.id, member.id, "sent", None)
                        sent += 1
                        continue
                    except Exception as e2:  # fall through to failure
                        err = str(e2)
                else:
                    err = str(e)
                failed += 1
                await self.db.log_send(guild.id, member.id, "failed", err)
            except Exception as e:
                failed += 1
                await self.db.log_send(guild.id, member.id, "failed", str(e))
        eta = total * self.rate_limiter.min_interval
        return total, sent, failed, eta
