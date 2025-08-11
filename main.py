from __future__ import annotations

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import EnvConfig
from db import Database
from dm_queue import DMQueue
from embeds import build_reminder_embed, build_status_embed, build_summary_embed
from scheduler import Scheduler

intents = discord.Intents.none()
intents.guilds = True
intents.members = True


class StaffBot(commands.Bot):
    def __init__(self, config: EnvConfig) -> None:
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.db = Database()
        self.dm_queue = DMQueue(self.db)
        self.scheduler = Scheduler(self, self.db, self.dm_queue)

    async def setup_hook(self) -> None:
        await self.db.connect()
        self.scheduler.start()
        for guild in self.guilds:
            cfg = await self.db.get_guild_config(guild.id)
            if cfg.schedule_cron:
                self.scheduler.schedule_guild(guild.id, cfg)
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({self.user.id})")

    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.db.get_guild_config(guild.id)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        self.scheduler.cancel_guild(guild.id)


bot_config = EnvConfig()
bot = StaffBot(bot_config)


def manager_only():
    async def predicate(inter: discord.Interaction) -> bool:
        if inter.user.guild_permissions.administrator:
            return True
        role = inter.guild.get_role(bot_config.manager_role_id)
        if role and role in inter.user.roles:
            return True
        raise app_commands.CheckFailure("Not authorized")

    return app_commands.check(predicate)


staff_group = app_commands.Group(name="staff", description="Staff reminders")


@staff_group.command(name="setrole", description="Set staff role")
@manager_only()
async def setrole(inter: discord.Interaction, role: discord.Role) -> None:
    cfg = await bot.db.update_guild_config(inter.guild.id, staff_role_id=role.id)
    queued = len([m for m in role.members if not m.bot])
    embed = build_status_embed(cfg, inter.guild, queued)
    await inter.response.send_message(embed=embed, ephemeral=True)


@staff_group.command(name="setmessage", description="Set reminder message")
@manager_only()
async def setmessage(inter: discord.Interaction, text: str) -> None:
    message = text.replace("\\n", "\n")
    cfg = await bot.db.update_guild_config(inter.guild.id, reminder_message=message)
    role = inter.guild.get_role(cfg.staff_role_id) if cfg.staff_role_id else None
    queued = len([m for m in role.members if not m.bot]) if role else 0
    embed = build_status_embed(cfg, inter.guild, queued)
    await inter.response.send_message(embed=embed, ephemeral=True)


remind_group = app_commands.Group(name="remind", description="Reminder actions")


@remind_group.command(name="now", description="Send reminders now")
@manager_only()
async def remind_now(inter: discord.Interaction) -> None:
    cfg = await bot.db.get_guild_config(inter.guild.id)
    total, sent, failed, eta = await bot.dm_queue.send(inter.guild, cfg)
    await bot.db.update_guild_config(inter.guild.id, last_sent_at=datetime.utcnow().isoformat())
    embed = build_summary_embed(total, sent, failed, eta)
    await inter.response.send_message(embed=embed, ephemeral=True)


@staff_group.command(name="status", description="Show current status")
async def status(inter: discord.Interaction) -> None:
    cfg = await bot.db.get_guild_config(inter.guild.id)
    role = inter.guild.get_role(cfg.staff_role_id) if cfg.staff_role_id else None
    queued = len([m for m in role.members if not m.bot]) if role else 0
    embed = build_status_embed(cfg, inter.guild, queued)
    await inter.response.send_message(embed=embed, ephemeral=True)


@staff_group.command(name="test", description="DM yourself a reminder")
async def test(inter: discord.Interaction) -> None:
    cfg = await bot.db.get_guild_config(inter.guild.id)
    message = cfg.reminder_message.replace("\\n", "\n")
    embed = build_reminder_embed(inter.guild.name, message)
    await inter.user.send(embed=embed)
    await inter.response.send_message(embed=discord.Embed(description="Sent"), ephemeral=True)


schedule_group = app_commands.Group(name="schedule", description="Scheduling")


@schedule_group.command(name="set", description="Set schedule")
@manager_only()
async def schedule_set(inter: discord.Interaction, cron: str) -> None:
    cfg = await bot.db.update_guild_config(inter.guild.id, schedule_cron=cron)
    bot.scheduler.schedule_guild(inter.guild.id, cfg)
    await inter.response.send_message(embed=discord.Embed(description="Scheduled"), ephemeral=True)


@schedule_group.command(name="clear", description="Clear schedule")
@manager_only()
async def schedule_clear(inter: discord.Interaction) -> None:
    await bot.db.update_guild_config(inter.guild.id, schedule_cron=None)
    bot.scheduler.cancel_guild(inter.guild.id)
    await inter.response.send_message(embed=discord.Embed(description="Cleared"), ephemeral=True)

staff_group.add_command(remind_group)
staff_group.add_command(schedule_group)
bot.tree.add_command(staff_group)


@bot.tree.error
async def on_app_command_error(inter: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if inter.response.is_done():
            await inter.followup.send(embed=discord.Embed(description="Not authorized"), ephemeral=True)
        else:
            await inter.response.send_message(embed=discord.Embed(description="Not authorized"), ephemeral=True)
    else:
        raise error


if __name__ == "__main__":
    bot.run(bot_config.token)
