import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message, save_reaction_roles
from config.settings import STAFF_ROLE_NAME, UNASSIGNED_ROLE_NAME, REACTION_ROLE_CHANNELS

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reaction_roles = {}

    async def create_class_selection_message(self, channel: discord.TextChannel, semester: int, class_count: int) -> discord.Message:
        """クラス選択用のリアクションロールメッセージを作成する"""
        # メッセージの内容を作成
        content = f"## {semester}期のクラス選択\n"
        content += f"<@&{discord.utils.get(channel.guild.roles, name=UNASSIGNED_ROLE_NAME).id}> 以下のリアクションをクリックして、あなたのクラスを選択してください：\n\n"
        
        # ロールと絵文字の対応を設定
        role_emojis = {}
        for i in range(1, class_count + 1):
            role_emojis[f"{semester}-{i}生徒"] = f"{i}️⃣"
        
        # メッセージにロールの説明を追加
        for role_name, emoji in role_emojis.items():
            content += f"{emoji} - {role_name}\n"
        
        # メッセージを送信
        message = await channel.send(content)
        
        # リアクションを追加
        for emoji in role_emojis.values():
            await message.add_reaction(emoji)
        
        # リアクションロールの設定を保存
        self.reaction_roles[message.id] = {
            "roles": [discord.utils.get(channel.guild.roles, name=role_name) for role_name in role_emojis.keys()],
            "emojis": role_emojis
        }
        
        # 設定をJSONファイルに保存
        save_reaction_roles(self.reaction_roles)
        
        return message

    async def create_reaction_role_message(self, channel: discord.TextChannel, roles: list, semester: int) -> discord.Message:
        """リアクションロールのメッセージを作成する"""
        # メッセージの内容を作成
        staff_role = discord.utils.get(channel.guild.roles, name=STAFF_ROLE_NAME)
        content = f"## {staff_role.mention} 各位。{semester}期のロールを選択してください。\n"
        content += "以下のリアクションをクリックして、あなたの担当クラスを選択してください：\n\n"
        
        # ロールと絵文字の対応を設定
        role_emojis = {}
        for i in range(1, len(roles) + 1):
            role_emojis[f"{semester}-{i}職員"] = f"{i}️⃣"
        
        # メッセージにロールの説明を追加
        for role_name, emoji in role_emojis.items():
            content += f"{emoji} - {role_name}\n"
        
        # メッセージを送信
        message = await channel.send(content)
        
        # リアクションを追加
        for emoji in role_emojis.values():
            await message.add_reaction(emoji)
        
        # リアクションロールの設定を保存
        self.reaction_roles[message.id] = {
            "roles": [discord.utils.get(channel.guild.roles, name=role_name) for role_name in role_emojis.keys()],
            "emojis": role_emojis
        }
        
        # 設定をJSONファイルに保存
        save_reaction_roles(self.reaction_roles)
        
        return message

    async def create_reaction_roles_internal(self, guild, semester, class_count):
        semester_student_role = discord.utils.get(guild.roles, name=f"{semester}期生")
        semester_teacher_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
        if not semester_student_role or not semester_teacher_role:
            raise Exception(f"{semester}期のロールが見つかりません。先にロールを作成してください。")
        teacher_roles = []
        for i in range(1, class_count + 1):
            teacher_role = discord.utils.get(guild.roles, name=f"{semester}-{i}職員")
            if teacher_role:
                teacher_roles.append(teacher_role)
        
        # 職員用リアクションロールチャンネルの取得
        staff_channel = next((channel for channel in guild.text_channels if REACTION_ROLE_CHANNELS["staff"] in channel.name), None)
        if staff_channel:
            await self.create_reaction_role_message(staff_channel, teacher_roles, semester)
        else:
            raise Exception(f"職員用リアクションロールチャンネル（{REACTION_ROLE_CHANNELS['staff']}）が見つかりません。")
        
        # 生徒用リアクションロールチャンネルの取得
        student_channel = next((channel for channel in guild.text_channels if REACTION_ROLE_CHANNELS["student"] in channel.name), None)
        if student_channel:
            await self.create_class_selection_message(student_channel, semester, class_count)
        else:
            raise Exception(f"生徒用リアクションロールチャンネル（{REACTION_ROLE_CHANNELS['student']}）が見つかりません。")

    @app_commands.command(name="create_reaction_roles", description="指定した学期のリアクションロールメッセージを作成します")
    @app_commands.describe(
        semester="学期（数字）",
        class_count="クラス数"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def create_reaction_roles(self, interaction: discord.Interaction, semester: int, class_count: int):
        try:
            await interaction.response.send_message('リアクションロールメッセージを作成中です...')
            await self.create_reaction_roles_internal(interaction.guild, semester, class_count)
            await interaction.followup.send(
                f'✅ リアクションロールメッセージを作成しました。'
            )
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        # メッセージIDがリアクションロールの設定に含まれているか確認
        if payload.message_id in self.reaction_roles:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            emoji = str(payload.emoji)
            
            # 絵文字に対応するロールを取得
            role_type = None
            for role_type_name, role_emoji in self.reaction_roles[payload.message_id]["emojis"].items():
                if emoji == role_emoji:
                    role_type = role_type_name
                    break
            
            if role_type:
                # 対応するロールを探して付与
                for role in self.reaction_roles[payload.message_id]["roles"]:
                    if role.name == role_type:
                        await member.add_roles(role)
                        # クラスロールの場合、期生のロールも付与
                        if role.name.endswith("生徒"):
                            semester = role.name.split("-")[0]  # 期数を取得
                            semester_role = discord.utils.get(guild.roles, name=f"{semester}期生")
                            if semester_role:
                                await member.add_roles(semester_role)
                        # 職員ロールの場合、期職員のロールも付与
                        elif role.name.endswith("職員"):
                            semester = role.name.split("-")[0]  # 期数を取得
                            semester_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
                            if semester_role:
                                await member.add_roles(semester_role)
                        
                        # ロール未付与ロールを削除
                        unassigned_role = discord.utils.get(guild.roles, name=UNASSIGNED_ROLE_NAME)
                        if unassigned_role and unassigned_role in member.roles:
                            await member.remove_roles(unassigned_role)
                        
                        # 管理用チャンネルを取得
                        admin_channel = next((channel for channel in guild.text_channels if "管理bot" in channel.name), None)
                        if admin_channel:
                            await admin_channel.send(f"`{member.name}` に `{role.name}` ロールを付与しました。")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        
        # メッセージIDがリアクションロールの設定に含まれているか確認
        if payload.message_id in self.reaction_roles:
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            emoji = str(payload.emoji)
            
            # 絵文字に対応するロールを取得
            role_type = None
            for role_type_name, role_emoji in self.reaction_roles[payload.message_id]["emojis"].items():
                if emoji == role_emoji:
                    role_type = role_type_name
                    break
            
            if role_type:
                # 対応するロールを探して削除
                for role in self.reaction_roles[payload.message_id]["roles"]:
                    if role.name == role_type:
                        await member.remove_roles(role)
                        # クラスロールの場合、期生のロールも削除
                        if role.name.endswith("生徒"):
                            semester = role.name.split("-")[0]  # 期数を取得
                            semester_role = discord.utils.get(guild.roles, name=f"{semester}期生")
                            if semester_role:
                                await member.remove_roles(semester_role)
                        # 職員ロールの場合、期職員のロールも削除
                        elif role.name.endswith("職員"):
                            semester = role.name.split("-")[0]  # 期数を取得
                            semester_role = discord.utils.get(guild.roles, name=f"{semester}期職員")
                            if semester_role:
                                await member.remove_roles(semester_role)
                        
                        # ロール未付与ロールを付与
                        unassigned_role = discord.utils.get(guild.roles, name=UNASSIGNED_ROLE_NAME)
                        if unassigned_role and unassigned_role not in member.roles:
                            await member.add_roles(unassigned_role)
                        
                        # 管理用チャンネルを取得
                        admin_channel = next((channel for channel in guild.text_channels if "管理bot" in channel.name), None)
                        if admin_channel:
                            await admin_channel.send(f"`{member.name}` から `{role.name}` ロールを削除しました。")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot)) 