import discord
from discord.ext import commands
import traceback
import sys

from config.settings import DISCORD_TOKEN, COMMAND_PREFIX
from utils.helpers import load_reaction_roles

# Botの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を読み取るために必要
intents.members = True         # メンバー情報を取得するために必要
intents.presences = True       # プレゼンス情報を取得するために必要

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Botが起動したときの処理
@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました')
    try:
        # リアクションロールの設定を読み込む
        reaction_roles = await load_reaction_roles(bot)
        # リアクションロールの設定をCogに渡す
        reaction_roles_cog = bot.get_cog("ReactionRoles")
        if reaction_roles_cog:
            reaction_roles_cog.reaction_roles = reaction_roles
        
        # 読み込まれているCogを確認
        print("\n読み込まれているCog:")
        for cog_name in bot.cogs:
            print(f"- {cog_name}")
        
        # スラッシュコマンドを同期
        print("\nスラッシュコマンドを同期しています...")
        synced = await bot.tree.sync()
        print(f"スラッシュコマンドを同期しました: {len(synced)}個")
        print("\n同期されたコマンド:")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# コマンドの例
@bot.command()
async def hello(ctx):
    await ctx.send('こんにちは！')

# Botの起動
async def main():
    async with bot:
        try:
            # 拡張機能を読み込む
            print("拡張機能を読み込んでいます...")
            await bot.load_extension('cogs.roles')
            await bot.load_extension('cogs.categories')
            await bot.load_extension('cogs.channels')
            await bot.load_extension('cogs.reaction_roles')
            await bot.load_extension('cogs.seasons')  # 新しいCogを読み込む
            print("拡張機能の読み込みが完了しました")
            
            # Botを起動
            await bot.start(DISCORD_TOKEN)
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            tb = traceback.format_exc()
            print(f"エラーが発生しました:")
            print(f"エラーの種類: {error_type}")
            print(f"エラーメッセージ: {error_msg}")
            print(f"トレースバック:\n{tb}")
            sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
