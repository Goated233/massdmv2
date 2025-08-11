from __future__ import annotations

import asyncio
import time
import logging
from typing import Callable, Tuple

import discord

from config import GuildConfig, render_message


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
        self.logger = logging.getLogger(__name__)

    async def log(self, guild: discord.Guild, cfg: GuildConfig, target: str, status: str, message: str, error: str | None = None) -> None:
        """Log message sending to console and optional log channel."""
        self.logger.info("%s -> %s: %s", status.upper(), target, message)
        if cfg.log_channel_id:
            channel = guild.get_channel(cfg.log_channel_id)
            if channel:
                embed = discord.Embed(title="Message Log")
                embed.add_field(name="Target", value=target, inline=False)
                embed.add_field(name="Status", value=status, inline=True)
                if error:
                    embed.add_field(name="Error", value=error, inline=False)
                embed.add_field(name="Message", value=message[:1024], inline=False)
                await channel.send(embed=embed)

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
            try:
                await member.send(msg)
                await self.db.log_send(guild.id, member.id, "sent", None)
                await self.log(guild, cfg, f"{member} ({member.id})", "sent", msg)
                sent += 1
            except discord.HTTPException as e:
                if e.status == 429 and getattr(e, "retry_after", None):
                    await asyncio.sleep(e.retry_after)
                    try:
                        await member.send(msg)
                        await self.db.log_send(guild.id, member.id, "sent", None)
                        await self.log(guild, cfg, f"{member} ({member.id})", "sent", msg)
                        sent += 1
                        continue
                    except Exception as e2:  # fall through to failure
                        err = str(e2)
                else:
                    err = str(e)
                failed += 1
                await self.db.log_send(guild.id, member.id, "failed", err)
                await self.log(guild, cfg, f"{member} ({member.id})", "failed", msg, err)
            except Exception as e:
                failed += 1
                err = str(e)
                await self.db.log_send(guild.id, member.id, "failed", err)
                await self.log(guild, cfg, f"{member} ({member.id})", "failed", msg, err)
        eta = total * self.rate_limiter.min_interval
        return total, sent, failed, eta
