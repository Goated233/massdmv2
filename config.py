from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Optional

from pydantic import BaseSettings

DEFAULT_MESSAGE = "Please review mod queue and tickets."


class EnvConfig(BaseSettings):
    """Environment configuration loaded from .env.

    The values are optional so the bot can start with a hardcoded token or
    without a manager role configured. Missing values default to ``None``.
    """

    token: str | None = None
    manager_role_id: int | None = None

    class Config:
        env_file = ".env"


@dataclass
class GuildConfig:
    guild_id: int
    staff_role_id: Optional[int] = None
    reminder_message: str = DEFAULT_MESSAGE
    schedule_cron: Optional[str] = None
    last_sent_at: Optional[str] = None  # ISO timestamp


def render_message(template: str, guild: str, user: str) -> str:
    """Render placeholders for guild, user and current ISO time."""
    now_iso = datetime.now(UTC).isoformat()
    return template.format(guild=guild, user=user, now_iso=now_iso)
