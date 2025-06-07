import discord
from discord import app_commands
from config.settings import EVENT_SETTINGS

def is_event_admin_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel.name != EVENT_SETTINGS["admin_channel"]:
            await interaction.response.send_message(
                f"❌ このコマンドは `{EVENT_SETTINGS['admin_channel']}` チャンネルでのみ実行できます。",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def has_event_admin_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not any(role.name == EVENT_SETTINGS["admin_role"] for role in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ このコマンドを実行するには `{EVENT_SETTINGS['admin_role']}` ロールが必要です。",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate) 