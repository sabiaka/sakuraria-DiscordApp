import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import format_error_message
from config.settings import EVENT_SETTINGS
from .checks import has_event_admin_role

class RoleManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add_role", description="イベントメンバーにロールを付与します")
    @app_commands.describe(
        user="ロールを付与するユーザー"
    )
    @has_event_admin_role()
    async def add_role(self, interaction: discord.Interaction, user: discord.Member):
        try:
            # 現在のチャンネル名からイベント名を取得
            channel_name = interaction.channel.name
            if not channel_name.startswith(EVENT_SETTINGS["role_assignment_channel_prefix"]):
                await interaction.response.send_message(
                    f"❌ このコマンドは `{EVENT_SETTINGS['role_assignment_channel_prefix']}` で始まるチャンネルでのみ使用できます。",
                    ephemeral=True
                )
                return

            event_name = channel_name.replace(EVENT_SETTINGS["role_assignment_channel_prefix"], "")
            event_role = discord.utils.get(interaction.guild.roles, name=f"🎯 {event_name}")

            if not event_role:
                await interaction.response.send_message(
                    f"❌ `{event_name}`のイベントロールが見つかりません。",
                    ephemeral=True
                )
                return

            # ユーザーが既にロールを持っているかチェック
            if event_role in user.roles:
                await interaction.response.send_message(
                    f"❌ {user.mention} は既に `{event_name}` ロールを持っています。",
                    ephemeral=True
                )
                return

            # ユーザーにロールを付与
            await user.add_roles(event_role)
            
            # 成功メッセージを送信
            await interaction.response.send_message(
                f"✅ {user.mention} に `{event_name}` ロールを付与しました。"
            )

        except Exception as e:
            await interaction.response.send_message(format_error_message(e))

    @app_commands.command(name="remove_role", description="イベントメンバーからロールを削除します")
    @app_commands.describe(
        user="ロールを削除するユーザー"
    )
    @has_event_admin_role()
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member):
        try:
            # 現在のチャンネル名からイベント名を取得
            channel_name = interaction.channel.name
            if not channel_name.startswith(EVENT_SETTINGS["role_assignment_channel_prefix"]):
                await interaction.response.send_message(
                    f"❌ このコマンドは `{EVENT_SETTINGS['role_assignment_channel_prefix']}` で始まるチャンネルでのみ使用できます。",
                    ephemeral=True
                )
                return

            event_name = channel_name.replace(EVENT_SETTINGS["role_assignment_channel_prefix"], "")
            event_role = discord.utils.get(interaction.guild.roles, name=f"🎯 {event_name}")

            if not event_role:
                await interaction.response.send_message(
                    f"❌ `{event_name}`のイベントロールが見つかりません。",
                    ephemeral=True
                )
                return

            # ユーザーがロールを持っているかチェック
            if event_role not in user.roles:
                await interaction.response.send_message(
                    f"❌ {user.mention} は `{event_name}` ロールを持っていません。",
                    ephemeral=True
                )
                return

            # ユーザーからロールを削除
            await user.remove_roles(event_role)
            
            # 成功メッセージを送信
            await interaction.response.send_message(
                f"✅ {user.mention} から `{event_name}` ロールを削除しました。"
            )

        except Exception as e:
            await interaction.response.send_message(format_error_message(e))

async def setup(bot: commands.Bot):
    await bot.add_cog(RoleManagement(bot)) 