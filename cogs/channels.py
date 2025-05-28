import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message, get_category_by_name

class Channels(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_channels_internal(self, guild, semester, class_count):
        teacher_category = get_category_by_name(guild, f"👨‍🏫 {semester}期職員")
        student_category = get_category_by_name(guild, f"👨‍🎓 {semester}期生徒")
        if not teacher_category or not student_category:
            raise Exception(f"{semester}期のカテゴリが見つかりません。先にカテゴリを作成してください。")
        semester_student_role = discord.utils.get(guild.roles, name=f"{semester}期生")
        semester_teacher_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
        if not semester_student_role or not semester_teacher_role:
            raise Exception(f"{semester}期のロールが見つかりません。先にロールを作成してください。")
        overwrites_semester_channel = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            semester_student_role: discord.PermissionOverwrite(view_channel=True),
            semester_teacher_role: discord.PermissionOverwrite(view_channel=True)
        }
        await guild.create_text_channel(
            name=f"📗📢｜{semester}期連絡",
            category=student_category,
            overwrites=overwrites_semester_channel
        )
        for i in range(1, class_count + 1):
            await guild.create_text_channel(
                name=f"📗📝｜{semester}-{i}教員",
                category=teacher_category
            )
        for i in range(1, class_count + 1):
            student_role = discord.utils.get(guild.roles, name=f"{semester}-{i}生徒")
            overwrites_class_channel = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                student_role: discord.PermissionOverwrite(view_channel=True, send_messages=True),
                semester_teacher_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            await guild.create_text_channel(
                name=f"📗💬｜{semester}-{i}雑談",
                category=student_category,
                overwrites=overwrites_class_channel
            )
            await guild.create_text_channel(
                name=f"📗📸｜{semester}-{i}写真",
                category=student_category,
                overwrites=overwrites_class_channel
            )
            await guild.create_text_channel(
                name=f"📗📢｜{semester}-{i}連絡",
                category=student_category,
                overwrites=overwrites_class_channel
            )

    @app_commands.command(name="create_channels", description="指定した学期のチャンネルを作成します")
    @app_commands.describe(
        semester="学期（数字）",
        class_count="クラス数"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def create_channels(self, interaction: discord.Interaction, semester: int, class_count: int):
        try:
            await interaction.response.send_message('チャンネルを作成中です...')
            await self.create_channels_internal(interaction.guild, semester, class_count)
            await interaction.followup.send(
                f'✅ 以下のチャンネルを作成しました：\n'
                f'📁 👨‍🏫 {semester}期職員\n'
                f'  └ {class_count}個の教員用チャンネル\n'
                f'📁 👨‍🎓 {semester}期生徒\n'
                f'  └ 期全体連絡チャンネル\n'
                f'  └ {class_count}クラス × 3チャンネル（雑談・写真・連絡）'
            )
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @app_commands.command(name="next_season", description="指定した学期の生徒にOBロールを付与し、チャンネル名を更新します")
    @app_commands.describe(
        semester="学期（数字）"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def next_season(self, interaction: discord.Interaction, semester: int):
        try:
            await interaction.response.send_message('OBロールの付与とチャンネル名の更新を開始します...')

            # 期生ロールの存在確認
            semester_student_role = discord.utils.get(interaction.guild.roles, name=f"{semester}期生")
            if not semester_student_role:
                await interaction.followup.send(f'❌ {semester}期生のロールが見つかりません。')
                return

            # OBロールの存在確認
            ob_role = discord.utils.get(interaction.guild.roles, name="OB")
            if not ob_role:
                await interaction.followup.send('❌ OBロールが見つかりません。先に /create_first_roll コマンドを実行してください。')
                return

            # 期生ロールを持つメンバーを取得
            members_with_role = semester_student_role.members
            if not members_with_role:
                await interaction.followup.send(f'⚠️ {semester}期生のロールを持つメンバーが見つかりません。処理を続行します。')
                members_with_role = []

            # 1期生の場合、既にOBロールを持っているかチェック
            if semester == 1:
                for member in members_with_role:
                    if ob_role in member.roles:
                        await interaction.followup.send(f'❌ 1期生のメンバーは既にOBロールを持っています。このコマンドは実行できません。')
                        return

            # OBロールを付与
            updated_members = []
            for member in members_with_role:
                if ob_role not in member.roles:
                    await member.add_roles(ob_role)
                    updated_members.append(member.name)

            # チャンネル名の更新
            updated_channels = []
            for channel in interaction.guild.text_channels:
                if channel.name.startswith(f"📗") and str(semester) in channel.name:
                    new_name = channel.name.replace("📗", "📙", 1)
                    await channel.edit(name=new_name)
                    updated_channels.append(channel.name)

            # 結果を報告
            result_message = []
            
            if updated_members:
                result_message.append(
                    f'✅ 以下のメンバーにOBロールを付与しました：\n'
                    f'{chr(10).join([f"- {name}" for name in updated_members])}'
                )
            else:
                if members_with_role:
                    result_message.append(f'ℹ️ {semester}期生のメンバーは既にOBロールを持っています。')

            if updated_channels:
                result_message.append(
                    f'✅ 以下のチャンネルの名前を更新しました：\n'
                    f'{chr(10).join([f"- {name}" for name in updated_channels])}'
                )
            else:
                result_message.append(f'⚠️ 更新対象のチャンネルが見つかりませんでした。')

            await interaction.followup.send("\n\n".join(result_message))

        except Exception as e:
            await interaction.followup.send(format_error_message(e))

async def setup(bot: commands.Bot):
    await bot.add_cog(Channels(bot)) 