from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from pydantic import BaseSettings

DEFAULT_MESSAGE = "Please review mod queue and tickets."


class EnvConfig(BaseSettings):
    """Environment configuration loaded from .env."""

    token: str
    manager_role_id: int

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
    now_iso = datetime.utcnow().isoformat()
    return template.format(guild=guild, user=user, now_iso=now_iso)
