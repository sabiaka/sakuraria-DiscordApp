import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message, get_category_by_name

class Categories(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_categories_internal(self, guild, semester):
        teacher_category = get_category_by_name(guild, f"👨‍🏫 {semester}期職員")
        student_category = get_category_by_name(guild, f"👨‍🎓 {semester}期生徒")
        if teacher_category or student_category:
            raise Exception(f"{semester}期のカテゴリは既に存在します。")
        semester_teacher_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
        if not semester_teacher_role:
            raise Exception(f"{semester}期職員のロールが見つかりません。先にロールを作成してください。")
        teacher_category_name = f"👨‍🏫 {semester}期職員"
        overwrites_teacher_category = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            semester_teacher_role: discord.PermissionOverwrite(view_channel=True)
        }
        await guild.create_category(
            teacher_category_name,
            overwrites=overwrites_teacher_category
        )
        student_category_name = f"👨‍🎓 {semester}期生徒"
        await guild.create_category(student_category_name)

    @app_commands.command(name="create_categories", description="指定した学期のカテゴリを作成します")
    @app_commands.describe(
        semester="学期（数字）"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def create_categories(self, interaction: discord.Interaction, semester: int):
        try:
            await interaction.response.send_message('カテゴリを作成中です...')
            await self.create_categories_internal(interaction.guild, semester)
            await interaction.followup.send(
                f'✅ 以下のカテゴリを作成しました：\n'
                f'📁 👨‍🏫 {semester}期職員\n'
                f'📁 👨‍🎓 {semester}期生徒'
            )
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

async def setup(bot: commands.Bot):
    await bot.add_cog(Categories(bot)) 