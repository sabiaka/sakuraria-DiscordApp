import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import traceback
import sys

# 環境変数の読み込み
load_dotenv(dotenv_path='.env')  # 明示的に.envファイルを指定

# Botの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を読み取るために必要
intents.members = True         # メンバー情報を取得するために必要
intents.presences = True       # プレゼンス情報を取得するために必要
bot = commands.Bot(command_prefix='!', intents=intents)

# Botが起動したときの処理
@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました')
    try:
        synced = await bot.tree.sync()
        print(f"スラッシュコマンドを同期しました: {len(synced)}個")
    except Exception as e:
        print(f"スラッシュコマンドの同期に失敗しました: {e}")

# コマンドの例
@bot.command()
async def hello(ctx):
    await ctx.send('こんにちは！')

# カテゴリとチャンネルを作成するコマンド
@bot.tree.command(name="gen", description="教員向けと生徒向けのカテゴリとチャンネルを作成します")
@app_commands.describe(
    semester="学期（数字）",
    class_count="クラス数"
)
async def gen(interaction: discord.Interaction, semester: int, class_count: int):
    # 権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('このコマンドは管理者権限が必要です。')
        return

    try:
        # 処理開始を通知
        await interaction.response.send_message('チャンネルとロールを作成中です...')
        
        # 期全体のロールを作成
        semester_student_role = await interaction.guild.create_role(
            name=f"{semester}期生",
            color=discord.Color.blue(),
        )
        semester_teacher_role = await interaction.guild.create_role(
            name=f"{semester}期職員",
            color=discord.Color.green()
        )
        
        # クラスごとのロールを作成
        class_roles = []
        for i in range(1, class_count + 1):
            student_role = await interaction.guild.create_role(
                name=f"{semester}-{i}生徒",
                color=discord.Color.blue(),
                hoist=True  # オンラインメンバーとは別にロールメンバーを表示
            )
            teacher_role = await interaction.guild.create_role(
                name=f"{semester}-{i}職員",
                color=discord.Color.green()
            )
            class_roles.extend([student_role, teacher_role])
        
        # 教員用カテゴリの作成
        teacher_category_name = f"👨‍🏫 {semester}期職員"
        teacher_category = await interaction.guild.create_category(teacher_category_name)
        
        # 生徒用カテゴリの作成
        student_category_name = f"👨‍🎓 {semester}期生徒"
        student_category = await interaction.guild.create_category(student_category_name)
        
        # 期全体の連絡チャンネルを作成
        await interaction.guild.create_text_channel(
            name=f"📢｜{semester}期連絡",
            category=student_category
        )
        
        # 教員用チャンネルの作成
        for i in range(1, class_count + 1):
            channel_name = f"📝｜{semester}-{i}教員"
            await interaction.guild.create_text_channel(
                name=channel_name,
                category=teacher_category
            )
        
        # 生徒用チャンネルの作成
        for i in range(1, class_count + 1):
            # 雑談チャンネル
            await interaction.guild.create_text_channel(
                name=f"💬｜{semester}-{i}雑談",
                category=student_category
            )
            # 写真チャンネル
            await interaction.guild.create_text_channel(
                name=f"📸｜{semester}-{i}写真",
                category=student_category
            )
            # 連絡チャンネル
            await interaction.guild.create_text_channel(
                name=f"📢｜{semester}-{i}連絡",
                category=student_category
            )
        
        await interaction.followup.send(
            f'✅ 以下のカテゴリ、チャンネル、ロールを作成しました：\n'
            f'📁 {teacher_category_name}\n'
            f'  └ {class_count}個の教員用チャンネル\n'
            f'📁 {student_category_name}\n'
            f'  └ 期全体連絡チャンネル\n'
            f'  └ {class_count}クラス × 3チャンネル（雑談・写真・連絡）\n'
            f'👥 ロール\n'
            f'  └ {semester}期生\n'
            f'  └ {semester}期職員\n'
            f'  └ {class_count}クラス × 2ロール（生徒・職員）'
        )
    
    except discord.Forbidden:
        error_msg = (
            "❌ ボットに必要な権限がありません。\n"
            "必要な権限:\n"
            "- チャンネルの管理\n"
            "- ロールの管理\n"
            "- カテゴリの管理"
        )
        await interaction.followup.send(error_msg)
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        tb = traceback.format_exc()
        error_details = (
            f"❌ エラーが発生しました:\n"
            f"エラーの種類: {error_type}\n"
            f"エラーメッセージ: {error_msg}\n"
            f"```\n{tb}\n```"
        )
        await interaction.followup.send(error_details)


# カテゴリとチャンネルを削除するコマンド
@bot.tree.command(name="delete", description="指定した学期の教員向けと生徒向けカテゴリとチャンネルを削除します")
@app_commands.describe(
    start_semester="削除開始学期（数字）",
    end_semester="削除終了学期（数字、省略可）"
)
async def delete(interaction: discord.Interaction, start_semester: int, end_semester: int = None):
    # 権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('このコマンドは管理者権限が必要です。')
        return

    try:
        # 終了学期が指定されていない場合は開始学期のみを対象とする
        if end_semester is None:
            end_semester = start_semester
        
        # 開始学期が終了学期より大きい場合は入れ替える
        if start_semester > end_semester:
            start_semester, end_semester = end_semester, start_semester

        # 削除対象のカテゴリとロールを検索
        categories_to_delete = []
        roles_to_delete = []
        
        for semester in range(start_semester, end_semester + 1):
            # 教員用カテゴリの検索（結合された絵文字と分解された絵文字の両方に対応）
            teacher_category = discord.utils.get(interaction.guild.categories, name=f"👨‍🏫 {semester}期職員")
            if not teacher_category:
                teacher_category = discord.utils.get(interaction.guild.categories, name=f"👨🏫 {semester}期職員")
            
            # 生徒用カテゴリの検索（結合された絵文字と分解された絵文字の両方に対応）
            student_category = discord.utils.get(interaction.guild.categories, name=f"👨‍🎓 {semester}期生徒")
            if not student_category:
                student_category = discord.utils.get(interaction.guild.categories, name=f"👨🎓 {semester}期生徒")
            
            if teacher_category:
                categories_to_delete.append(("教員", teacher_category))
            if student_category:
                categories_to_delete.append(("生徒", student_category))
            
            # ロールの検索
            semester_student_role = discord.utils.get(interaction.guild.roles, name=f"{semester}期生")
            semester_teacher_role = discord.utils.get(interaction.guild.roles, name=f"{semester}期職員")
            
            if semester_student_role:
                roles_to_delete.append(("期生", semester_student_role))
            if semester_teacher_role:
                roles_to_delete.append(("期職員", semester_teacher_role))
            
            # クラスごとのロールを検索
            for role in interaction.guild.roles:
                if role.name.startswith(f"{semester}-") and (role.name.endswith("生徒") or role.name.endswith("職員")):
                    role_type = "生徒" if role.name.endswith("生徒") else "職員"
                    roles_to_delete.append((f"クラス{role_type}", role))

        if not categories_to_delete and not roles_to_delete:
            await interaction.response.send_message(
                f'❌ {start_semester}期から{end_semester}期のカテゴリとロールが見つかりません。'
            )
            return

        # 確認ボタンの作成
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="削除する", style=discord.ButtonStyle.danger)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                await interaction.response.send_message("削除を開始します...")

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                await interaction.response.send_message("削除をキャンセルしました。")

        # 確認メッセージを送信
        view = ConfirmView()
        category_list = "\n".join([f"- {type_}用カテゴリ「{category.name}」" for type_, category in categories_to_delete])
        role_list = "\n".join([f"- {type_}ロール「{role.name}」" for type_, role in roles_to_delete])
        
        await interaction.response.send_message(
            f"⚠️ 本当に削除しますか？\n"
            f"以下のカテゴリとその中のすべてのチャンネル、およびロールが削除されます：\n"
            f"{category_list}\n"
            f"{role_list}\n"
            f"この操作は取り消せません。",
            view=view
        )

        # ユーザーの応答を待機
        await view.wait()

        if view.value:
            # カテゴリを削除
            deleted_categories = []
            for type_, category in categories_to_delete:
                # チャンネルを削除
                for channel in category.channels:
                    await channel.delete()
                
                # カテゴリを削除
                await category.delete()
                deleted_categories.append(f"{type_}用カテゴリ「{category.name}」")
            
            # ロールを削除
            deleted_roles = []
            for type_, role in roles_to_delete:
                await role.delete()
                deleted_roles.append(f"{type_}ロール「{role.name}」")
            
            await interaction.followup.send(
                f'✅ 以下のカテゴリ、チャンネル、ロールを削除しました：\n'
                f'{chr(10).join(deleted_categories)}\n'
                f'{chr(10).join(deleted_roles)}'
            )
        else:
            await interaction.followup.send('❌ 削除をキャンセルしました。')

    except discord.Forbidden:
        error_msg = (
            "❌ ボットに必要な権限がありません。\n"
            "必要な権限:\n"
            "- チャンネルの管理\n"
            "- ロールの管理\n"
            "- カテゴリの管理"
        )
        await interaction.followup.send(error_msg)
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        tb = traceback.format_exc()
        error_details = (
            f"❌ エラーが発生しました:\n"
            f"エラーの種類: {error_type}\n"
            f"エラーメッセージ: {error_msg}\n"
            f"```\n{tb}\n```"
        )
        await interaction.followup.send(error_details)

# Botのトークンを環境変数から取得して起動
try:
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    bot.run(token)
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    tb = traceback.format_exc()
    print(f"エラーが発生しました:")
    print(f"エラーの種類: {error_type}")
    print(f"エラーメッセージ: {error_msg}")
    print(f"トレースバック:\n{tb}")
    sys.exit(1)