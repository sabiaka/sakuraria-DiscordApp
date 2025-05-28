import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message
from config.settings import STAFF_ROLE_NAME

class Roles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_roles_internal(self, guild, semester, class_count):
        semester_student_role = discord.utils.get(guild.roles, name=f"{semester}期生")
        semester_teacher_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
        if semester_student_role or semester_teacher_role:
            raise Exception(f"{semester}期のロールは既に存在します。")
        semester_student_role = await guild.create_role(
            name=f"{semester}期生",
            color=discord.Color.blue(),
        )
        semester_teacher_role = await guild.create_role(
            name=f"{semester}期職員",
            color=discord.Color.green()
        )
        for i in range(1, class_count + 1):
            await guild.create_role(
                name=f"{semester}-{i}生徒",
                color=discord.Color.blue(),
                hoist=True
            )
            await guild.create_role(
                name=f"{semester}-{i}職員",
                color=discord.Color.green()
            )

    @app_commands.command(name="create_roles", description="指定した学期のロールを作成します")
    @app_commands.describe(
        semester="学期（数字）",
        class_count="クラス数"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def create_roles(self, interaction: discord.Interaction, semester: int, class_count: int):
        try:
            await interaction.response.send_message('ロールを作成中です...')
            await self.create_roles_internal(interaction.guild, semester, class_count)
            await interaction.followup.send(
                f'✅ 以下のロールを作成しました：\n'
                f'👥 ロール\n'
                f'  └ {semester}期生\n'
                f'  └ {semester}期職員\n'
                f'  └ {class_count}クラス × 2ロール（生徒・職員）'
            )
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @app_commands.command(name="create_first_roll", description="職員とOBのロールを作成します")
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def create_first_roll(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_message('ロールを作成中です...')
            
            # 職員ロールの作成
            teacher_role = await interaction.guild.create_role(
                name=STAFF_ROLE_NAME,
                color=discord.Color.red(),
                hoist=True
            )
            
            # OBロールの作成
            ob_role = await interaction.guild.create_role(
                name="OB",
                color=discord.Color.blue()
            )
            
            await interaction.followup.send(
                f'✅ 以下のロールを作成しました：\n'
                f'👥 ロール\n'
                f'  └ {STAFF_ROLE_NAME}（赤色、オンラインメンバーとは別に表示）\n'
                f'  └ OB（青色）'
            )
        
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot)) 