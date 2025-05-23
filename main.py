import discord
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

# コマンドの例
@bot.command()
async def hello(ctx):
    await ctx.send('こんにちは！')

# カテゴリとチャンネルを作成するコマンド
@bot.command()
async def gen(ctx, semester: int, class_count: int):
    # 権限チェック
    if not ctx.author.guild_permissions.administrator:
        await ctx.send('このコマンドは管理者権限が必要です。')
        return

    try:
        # カテゴリの作成
        category_name = f"{semester}期職員"
        category = await ctx.guild.create_category(category_name)
        
        # チャンネルの作成
        for i in range(1, class_count + 1):
            channel_name = f"{semester} - {i}教員"
            await ctx.guild.create_text_channel(
                name=channel_name,
                category=category
            )
        
        await ctx.send(f'✅ カテゴリ「{category_name}」と{class_count}個のチャンネルを作成しました。')
    
    except discord.Forbidden:
        await ctx.send('❌ ボットに必要な権限がありません。')
    except Exception as e:
        await ctx.send(f'❌ エラーが発生しました: {str(e)}')

# Botのトークンを環境変数から取得して起動
try:
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    bot.run(token)
except Exception as e:
    print(f"エラーが発生しました: {e}")