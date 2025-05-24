import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

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
@bot.tree.command(name="gen", description="教員向けのカテゴリとチャンネルを作成します")
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
        await interaction.response.send_message('チャンネルを作成中です...')
        
        # カテゴリの作成
        category_name = f"{semester}期職員"
        category = await interaction.guild.create_category(category_name)
        
        # チャンネルの作成
        for i in range(1, class_count + 1):
            channel_name = f"{semester} - {i}教員"
            await interaction.guild.create_text_channel(
                name=channel_name,
                category=category
            )
        
        await interaction.followup.send(f'✅ カテゴリ「{category_name}」と{class_count}個のチャンネルを作成しました。')
    
    except discord.Forbidden:
        await interaction.followup.send('❌ ボットに必要な権限がありません。')
    except Exception as e:
        await interaction.followup.send(f'❌ エラーが発生しました: {str(e)}')

# カテゴリとチャンネルを削除するコマンド
@bot.tree.command(name="delete", description="指定した学期の教員向けカテゴリとチャンネルを削除します")
@app_commands.describe(
    semester="削除する学期（数字）"
)
async def delete(interaction: discord.Interaction, semester: int):
    # 権限チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message('このコマンドは管理者権限が必要です。')
        return

    try:
        # カテゴリを検索
        category_name = f"{semester}期職員"
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        
        if category is None:
            await interaction.response.send_message(f'❌ カテゴリ「{category_name}」が見つかりません。')
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
        await interaction.response.send_message(
            f"⚠️ 本当に削除しますか？\n"
            f"カテゴリ「{category_name}」とその中のすべてのチャンネルが削除されます。\n"
            f"この操作は取り消せません。",
            view=view
        )

        # ユーザーの応答を待機
        await view.wait()

        if view.value:
            # チャンネルを削除
            for channel in category.channels:
                await channel.delete()
            
            # カテゴリを削除
            await category.delete()
            
            await interaction.followup.send(f'✅ カテゴリ「{category_name}」とその中のチャンネルを削除しました。')
        else:
            await interaction.followup.send('❌ 削除をキャンセルしました。')

    except discord.Forbidden:
        await interaction.followup.send('❌ ボットに必要な権限がありません。')
    except Exception as e:
        await interaction.followup.send(f'❌ エラーが発生しました: {str(e)}')

# Botのトークンを環境変数から取得して起動
try:
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    bot.run(token)
except Exception as e:
    print(f"エラーが発生しました: {e}")