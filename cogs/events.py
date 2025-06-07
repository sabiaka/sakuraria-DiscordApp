import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import is_admin_channel, has_staff_role, is_administrator
from utils.helpers import format_error_message
from config.settings import EVENT_SETTINGS

def is_event_admin_channel():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.channel.name != EVENT_SETTINGS["admin_channel"]:
            await interaction.response.send_message(
                f"❌ このコマンドは `{EVENT_SETTINGS['admin_channel']}` チャンネルでのみ実行できます。",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def has_event_admin_role():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not any(role.name == EVENT_SETTINGS["admin_role"] for role in interaction.user.roles):
            await interaction.response.send_message(
                f"❌ このコマンドを実行するには `{EVENT_SETTINGS['admin_role']}` ロールが必要です。",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_event_internal(self, guild, event_name: str):
        # 1. イベント用のロールを作成
        event_role = await guild.create_role(
            name=f"🎯 {event_name}",
            color=discord.Color.purple(),
            hoist=True
        )

        # 2. カテゴリを作成
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            event_role: discord.PermissionOverwrite(view_channel=True)
        }
        
        category = await guild.create_category(
            name=event_name,
            overwrites=overwrites
        )

        # 3. チャンネルを作成
        channels = []
        channel_names = [
            f"ログ-{event_name}",
            f"ロール付与-{event_name}"
        ]

        for channel_name in channel_names:
            if "ログ" in channel_name:
                # フォーラムチャンネルを作成
                channel = await guild.create_forum(
                    name=channel_name,
                    category=category,
                    topic=f"{event_name}のログを記録するフォーラムです。"
                )
            else:
                channel = await guild.create_text_channel(
                    name=channel_name,
                    category=category
                )
                # ロール付与チャンネルに説明メッセージを投稿
                if "ロール付与" in channel_name:
                    embed = discord.Embed(
                        title="🎯 イベントロールの付与方法",
                        description=f"このチャンネルで以下のコマンドを使用して、`{event_name}`のメンバーを管理できます：",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="コマンド",
                        value=f"`/add_role [ユーザー名]`\n`/remove_role [ユーザー名]`",
                        inline=False
                    )
                    embed.add_field(
                        name="説明",
                        value=f"`/add_role` - 指定したユーザーに`{event_name}`ロールを付与します。\n`/remove_role` - 指定したユーザーから`{event_name}`ロールを削除します。",
                        inline=False
                    )
                    await channel.send(embed=embed)
            channels.append(channel)

        return category, channels, event_role

    async def delete_event_internal(self, guild, event_name: str):
        # 1. カテゴリを検索
        category = discord.utils.get(guild.categories, name=event_name)
        if not category:
            raise Exception(f"{event_name}のカテゴリが見つかりません。")

        # 2. カテゴリ内のチャンネルを削除
        channels_to_delete = []
        for channel in category.channels:
            channels_to_delete.append(channel)
        
        for channel in channels_to_delete:
            try:
                await channel.delete()
            except Exception as e:
                raise Exception(f"チャンネル {channel.name} の削除に失敗しました: {e}")

        # 3. カテゴリを削除
        try:
            await category.delete()
        except Exception as e:
            raise Exception(f"カテゴリ {event_name} の削除に失敗しました: {e}")

        # 4. ロールを削除
        role = discord.utils.get(guild.roles, name=f"🎯 {event_name}")
        if role:
            try:
                await role.delete()
            except Exception as e:
                raise Exception(f"ロール 🎯 {event_name} の削除に失敗しました: {e}")

    @app_commands.command(name="create_event", description="イベント用のカテゴリ、チャンネル、ロールを作成します")
    @app_commands.describe(
        event_name="イベント名"
    )
    @is_event_admin_channel()
    @has_event_admin_role()
    @is_administrator()
    async def create_event(self, interaction: discord.Interaction, event_name: str):
        try:
            await interaction.response.send_message('イベントの設定を開始します...')
            
            category, channels, role = await self.create_event_internal(interaction.guild, event_name)
            
            await interaction.followup.send(
                f'✅ {event_name}イベントの設定が完了しました：\n'
                f'👥 ロール\n'
                f'  └ 🎯 {event_name}\n'
                f'📁 カテゴリ\n'
                f'  └ {event_name}\n'
                f'💬 チャンネル\n'
                f'  └ ログ-{event_name}\n'
                f'  └ ロール付与-{event_name}'
            )
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @app_commands.command(name="delete_event", description="イベント用のカテゴリ、チャンネル、ロールを削除します")
    @app_commands.describe(
        event_name="イベント名"
    )
    @is_event_admin_channel()
    @has_event_admin_role()
    @is_administrator()
    async def delete_event(self, interaction: discord.Interaction, event_name: str):
        try:
            await interaction.response.send_message('イベントの削除を開始します...')
            
            # 確認メッセージの作成
            confirm_message = f"以下の削除を実行します：\n\n"
            confirm_message += f"📁 カテゴリ\n"
            confirm_message += f"  └ {event_name}\n"
            confirm_message += f"💬 チャンネル\n"
            confirm_message += f"  └ ログ-{event_name}\n"
            confirm_message += f"  └ ロール付与-{event_name}\n"
            confirm_message += f"👥 ロール\n"
            confirm_message += f"  └ 🎯 {event_name}\n\n"
            confirm_message += f"⚠️ この操作は取り消せません。実行してよろしいですか？"
            
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
                    
                    try:
                        await self.cog.delete_event_internal(interaction.guild, event_name)
                        await button_interaction.followup.send(
                            f'✅ {event_name}イベントの削除が完了しました。'
                        )
                    except Exception as e:
                        await button_interaction.followup.send(format_error_message(e))
                
                @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.secondary)
                async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id != interaction.user.id:
                        await button_interaction.response.send_message("この操作は実行できません。", ephemeral=True)
                        return
                    
                    await button_interaction.response.send_message("削除をキャンセルしました。")
            
            # 確認ビューを設定
            view = ConfirmView()
            view.cog = self
            
            await interaction.followup.send(confirm_message, view=view)
            
        except Exception as e:
            await interaction.followup.send(format_error_message(e))

    @app_commands.command(name="add_role", description="イベントメンバーにロールを付与します")
    @app_commands.describe(
        user="ロールを付与するユーザー"
    )
    @has_event_admin_role()
    async def add_role(self, interaction: discord.Interaction, user: discord.Member):
        try:
            # 現在のチャンネル名からイベント名を取得
            channel_name = interaction.channel.name
            if not channel_name.startswith(EVENT_SETTINGS["role_assignment_channel_prefix"]):
                await interaction.response.send_message(
                    f"❌ このコマンドは `{EVENT_SETTINGS['role_assignment_channel_prefix']}` で始まるチャンネルでのみ使用できます。",
                    ephemeral=True
                )
                return

            event_name = channel_name.replace(EVENT_SETTINGS["role_assignment_channel_prefix"], "")
            event_role = discord.utils.get(interaction.guild.roles, name=f"🎯 {event_name}")

            if not event_role:
                await interaction.response.send_message(
                    f"❌ `{event_name}`のイベントロールが見つかりません。",
                    ephemeral=True
                )
                return

            # ユーザーが既にロールを持っているかチェック
            if event_role in user.roles:
                await interaction.response.send_message(
                    f"❌ {user.mention} は既に `{event_name}` ロールを持っています。",
                    ephemeral=True
                )
                return

            # ユーザーにロールを付与
            await user.add_roles(event_role)
            
            # 成功メッセージを送信
            await interaction.response.send_message(
                f"✅ {user.mention} に `{event_name}` ロールを付与しました。"
            )

        except Exception as e:
            await interaction.response.send_message(
                format_error_message(e),
                ephemeral=True
            )

    @app_commands.command(name="remove_role", description="イベントメンバーからロールを削除します")
    @app_commands.describe(
        user="ロールを削除するユーザー"
    )
    @has_event_admin_role()
    async def remove_role(self, interaction: discord.Interaction, user: discord.Member):
        try:
            # 現在のチャンネル名からイベント名を取得
            channel_name = interaction.channel.name
            if not channel_name.startswith(EVENT_SETTINGS["role_assignment_channel_prefix"]):
                await interaction.response.send_message(
                    f"❌ このコマンドは `{EVENT_SETTINGS['role_assignment_channel_prefix']}` で始まるチャンネルでのみ使用できます。",
                    ephemeral=True
                )
                return

            event_name = channel_name.replace(EVENT_SETTINGS["role_assignment_channel_prefix"], "")
            event_role = discord.utils.get(interaction.guild.roles, name=f"🎯 {event_name}")

            if not event_role:
                await interaction.response.send_message(
                    f"❌ `{event_name}`のイベントロールが見つかりません。",
                    ephemeral=True
                )
                return

            # ユーザーがロールを持っているかチェック
            if event_role not in user.roles:
                await interaction.response.send_message(
                    f"❌ {user.mention} は `{event_name}` ロールを持っていません。",
                    ephemeral=True
                )
                return

            # ユーザーからロールを削除
            await user.remove_roles(event_role)
            
            # 成功メッセージを送信
            await interaction.response.send_message(
                f"✅ {user.mention} から `{event_name}` ロールを削除しました。"
            )

        except Exception as e:
            await interaction.response.send_message(
                format_error_message(e),
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot)) 