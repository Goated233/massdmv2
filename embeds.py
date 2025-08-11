from __future__ import annotations

from datetime import datetime

import discord

from config import GuildConfig


def build_reminder_embed(guild_name: str, message: str) -> discord.Embed:
    embed = discord.Embed(
        title="Staff Reminder",
        description=message,
        timestamp=datetime.utcnow(),
    )
    embed.set_footer(text=guild_name)
    return embed


def build_status_embed(cfg: GuildConfig, guild: discord.Guild, queued: int) -> discord.Embed:
    role = guild.get_role(cfg.staff_role_id) if cfg.staff_role_id else None
    desc = [
        f"**Staff role:** {role.mention if role else 'not set'}",
        f"**Message:** {cfg.reminder_message[:140]}",
        f"**Last sent:** {cfg.last_sent_at or 'never'}",
        f"**Schedule:** {cfg.schedule_cron or 'none'}",
        f"**Queued:** {queued}",
    ]
    return discord.Embed(title="Staff Reminder Status", description="\n".join(desc))


def build_summary_embed(total: int, sent: int, failed: int, eta: float) -> discord.Embed:
    desc = f"Total: {total}\nSent: {sent}\nFailed: {failed}\nEstimated time: {eta:.1f}s"
    return discord.Embed(title="Reminder Summary", description=desc)
