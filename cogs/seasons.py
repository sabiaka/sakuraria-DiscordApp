import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message, get_category_by_name
from config.settings import REACTION_ROLE_CHANNELS

class Seasons(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="new_season", description="新しい期のカテゴリとチャンネルを作成します")
    @app_commands.describe(
        semester="学期（数字）",
        class_count="クラス数"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def new_season(self, interaction: discord.Interaction, semester: int, class_count: int):
        try:
            await interaction.response.send_message('新しい期の設定を開始します...')
            
            # 1. ロールの作成
            try:
                roles_cog = self.bot.get_cog("Roles")
                if roles_cog:
                    await roles_cog.create_roles_internal(interaction.guild, semester, class_count)
                else:
                    await interaction.followup.send('❌ ロールの作成に失敗しました。')
                    return
            except Exception as e:
                await interaction.followup.send(f'❌ ロールの作成に失敗しました: {e}')
                return

            # 2. カテゴリの作成
            try:
                categories_cog = self.bot.get_cog("Categories")
                if categories_cog:
                    await categories_cog.create_categories_internal(interaction.guild, semester)
                else:
                    await interaction.followup.send('❌ カテゴリの作成に失敗しました。')
                    return
            except Exception as e:
                await interaction.followup.send(f'❌ カテゴリの作成に失敗しました: {e}')
                return

            # 3. チャンネルの作成
            try:
                channels_cog = self.bot.get_cog("Channels")
                if channels_cog:
                    await channels_cog.create_channels_internal(interaction.guild, semester, class_count)
                else:
                    await interaction.followup.send('❌ チャンネルの作成に失敗しました。')
                    return
            except Exception as e:
                await interaction.followup.send(f'❌ チャンネルの作成に失敗しました: {e}')
                return

            # 4. リアクションロールの作成
            try:
                reaction_roles_cog = self.bot.get_cog("ReactionRoles")
                if reaction_roles_cog:
                    await reaction_roles_cog.create_reaction_roles_internal(interaction.guild, semester, class_count)
                else:
                    await interaction.followup.send('❌ リアクションロールの作成に失敗しました。')
                    return
            except Exception as e:
                await interaction.followup.send(f'❌ リアクションロールの作成に失敗しました: {e}')
                return

            await interaction.followup.send(
                f'✅ {semester}期の設定が完了しました：\n'
                f'👥 ロール\n'
                f'  └ {semester}期生\n'
                f'  └ {semester}期職員\n'
                f'  └ {class_count}クラス × 2ロール（生徒・職員）\n'
                f'📁 カテゴリ\n'
                f'  └ 👨‍🏫 {semester}期職員\n'
                f'  └ 👨‍🎓 {semester}期生徒\n'
                f'💬 チャンネル\n'
                f'  └ 期全体連絡チャンネル\n'
                f'  └ {class_count}クラス × 3チャンネル（雑談・写真・連絡）\n'
                f'  └ {class_count}個の教員用チャンネル\n'
                f'🎯 リアクションロール\n'
                f'  └ 職員用のリアクションロール\n'
                f'  └ クラス選択用のリアクションロール'
            )

        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @app_commands.command(name="delete_season", description="指定した期のカテゴリとチャンネルを削除します")
    @app_commands.describe(
        start_semester="開始学期（数字）",
        end_semester="終了学期（数字、省略可）"
    )
    @is_admin_channel()
    @has_staff_role()
    @is_administrator()
    async def delete_season(self, interaction: discord.Interaction, start_semester: int, end_semester: int = None):
        try:
            await interaction.response.send_message('削除対象の確認中...')
            
            # 削除対象の確認
            categories_to_delete = []
            channels_to_delete = []
            roles_to_delete = []
            reaction_messages_to_delete = []
            
            # end_semesterが指定されていない場合は、start_semesterのみを処理
            end_semester = end_semester if end_semester is not None else start_semester
            
            # リアクションロールメッセージの検索
            for channel_type, channel_name in REACTION_ROLE_CHANNELS.items():
                channel = next((ch for ch in interaction.guild.text_channels if channel_name in ch.name), None)
                if channel:
                    try:
                        # チャンネルのメッセージを取得（最大100件）
                        async for message in channel.history(limit=100):
                            # メッセージの内容に学期番号が含まれているか確認
                            for semester in range(start_semester, end_semester + 1):
                                if f"{semester}期" in message.content:
                                    reaction_messages_to_delete.append(message)
                                    break
                    except Exception as e:
                        await interaction.followup.send(f"❌ チャンネル {channel.name} のメッセージ取得に失敗しました: {e}")
            
            for semester in range(start_semester, end_semester + 1):
                # カテゴリの確認
                teacher_category = get_category_by_name(interaction.guild, f"👨‍🏫 {semester}期職員")
                student_category = get_category_by_name(interaction.guild, f"👨‍🎓 {semester}期生徒")
                if teacher_category:
                    categories_to_delete.append(teacher_category)
                if student_category:
                    categories_to_delete.append(student_category)
                
                # チャンネルの確認
                for channel in interaction.guild.text_channels:
                    if str(semester) in channel.name:
                        channels_to_delete.append(channel)
                
                # ロールの確認
                semester_student_role = discord.utils.get(interaction.guild.roles, name=f"{semester}期生")
                semester_teacher_role = discord.utils.get(interaction.guild.roles, name=f"{semester}期職員")
                if semester_student_role:
                    roles_to_delete.append(semester_student_role)
                if semester_teacher_role:
                    roles_to_delete.append(semester_teacher_role)
                
                # クラスごとのロールの確認
                for i in range(1, 10):  # 最大9クラスまで確認
                    student_role = discord.utils.get(interaction.guild.roles, name=f"{semester}-{i}生徒")
                    teacher_role = discord.utils.get(interaction.guild.roles, name=f"{semester}-{i}職員")
                    if student_role:
                        roles_to_delete.append(student_role)
                    if teacher_role:
                        roles_to_delete.append(teacher_role)
            
            # 削除対象の表示
            if not categories_to_delete and not channels_to_delete and not roles_to_delete:
                await interaction.followup.send(f'❌ {start_semester}期から{end_semester}期の削除対象が見つかりませんでした。')
                return
            
            # 確認メッセージの作成
            confirm_message = f"以下の削除を実行します：\n\n"
            
            if categories_to_delete:
                confirm_message += "📁 カテゴリ\n"
                for category in categories_to_delete:
                    confirm_message += f"  └ {category.name}\n"
            
            if channels_to_delete:
                confirm_message += "\n💬 チャンネル\n"
                for channel in channels_to_delete:
                    confirm_message += f"  └ {channel.name}\n"
            
            if roles_to_delete:
                confirm_message += "\n👥 ロール\n"
                for role in roles_to_delete:
                    confirm_message += f"  └ {role.name}\n"
            
            if reaction_messages_to_delete:
                confirm_message += "\n🎯 リアクションロールメッセージ\n"
                for message in reaction_messages_to_delete:
                    confirm_message += f"  └ {message.channel.name}のメッセージ\n"
            
            confirm_message += "\n⚠️ この操作は取り消せません。実行してよろしいですか？"
            
            # 確認ボタンの作成
            class ConfirmView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                
                @discord.ui.button(label="実行", style=discord.ButtonStyle.danger)
                async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("この操作は実行できません。", ephemeral=True)
                        return
                    
                    await button_interaction.response.send_message("削除を開始します...")
                    
                    # カテゴリの削除
                    for category in categories_to_delete:
                        try:
                            await category.delete()
                        except Exception as e:
                            await button_interaction.followup.send(f"❌ カテゴリ {category.name} の削除に失敗しました: {e}")
                    
                    # チャンネルの削除
                    for channel in channels_to_delete:
                        try:
                            await channel.delete()
                        except Exception as e:
                            await button_interaction.followup.send(f"❌ チャンネル {channel.name} の削除に失敗しました: {e}")
                    
                    # ロールの削除
                    for role in roles_to_delete:
                        try:
                            await role.delete()
                        except Exception as e:
                            await button_interaction.followup.send(f"❌ ロール {role.name} の削除に失敗しました: {e}")
                    
                    # リアクションロールメッセージの削除
                    for message in reaction_messages_to_delete:
                        try:
                            await message.delete()
                        except Exception as e:
                            await button_interaction.followup.send(f"❌ リアクションロールメッセージの削除に失敗しました: {e}")
                    
                    await button_interaction.followup.send("✅ 削除が完了しました。")
                    self.stop()
                
                @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
                async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("この操作は実行できません。", ephemeral=True)
                        return
                    
                    await button_interaction.response.send_message("操作をキャンセルしました。")
                    self.stop()
            
            await interaction.followup.send(confirm_message, view=ConfirmView())

        except Exception as e:
            await interaction.followup.send(format_error_message(e))

async def setup(bot: commands.Bot):
    await bot.add_cog(Seasons(bot)) 