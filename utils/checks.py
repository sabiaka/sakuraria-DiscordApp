import discord
from config.settings import ADMIN_CHANNEL_NAME, STAFF_ROLE_NAME

def is_admin_channel():
    """管理botチャンネルでのみコマンドを使用可能にするデコレータ"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.channel.name.startswith(ADMIN_CHANNEL_NAME):
            await interaction.response.send_message(
                f'このコマンドは「{ADMIN_CHANNEL_NAME}」チャンネルでのみ使用できます。',
                ephemeral=True
            )
            return False
        return True
    return discord.app_commands.check(predicate)

def has_staff_role():
    """職員ロールを持つユーザーのみコマンドを使用可能にするデコレータ"""
    async def predicate(interaction: discord.Interaction) -> bool:
        staff_role = discord.utils.get(interaction.guild.roles, name=STAFF_ROLE_NAME)
        if not staff_role or staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                f'このコマンドは「{STAFF_ROLE_NAME}」ロールを持つユーザーのみが使用できます。',
                ephemeral=True
            )
            return False
        return True
    return discord.app_commands.check(predicate)

def is_administrator():
    """管理者権限を持つユーザーのみコマンドを使用可能にするデコレータ"""
    async def predicate(interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                'このコマンドは管理者権限が必要です。',
                ephemeral=True
            )
            return False
        return True
    return discord.app_commands.check(predicate) 