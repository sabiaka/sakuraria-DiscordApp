import json
import os
import traceback
from typing import Dict, List, Optional, Tuple, Union

import discord

def save_reaction_roles(reaction_roles: Dict) -> None:
    """リアクションロールの設定をJSONファイルに保存する"""
    serializable_roles = {}
    for message_id, data in reaction_roles.items():
        serializable_roles[str(message_id)] = {
            "roles": [role.id for role in data["roles"]],
            "emojis": data["emojis"]
        }
    
    with open('reaction_roles.json', 'w', encoding='utf-8') as f:
        json.dump(serializable_roles, f, ensure_ascii=False, indent=4)

async def load_reaction_roles(bot) -> Dict:
    """リアクションロールの設定をJSONファイルから読み込む"""
    reaction_roles = {}
    if not os.path.exists('reaction_roles.json'):
        print("リアクションロールの設定ファイルが見つかりません。")
        return reaction_roles
    
    with open('reaction_roles.json', 'r', encoding='utf-8') as f:
        serializable_roles = json.load(f)
    
    loaded_count = 0
    for message_id, data in serializable_roles.items():
        roles = []
        for guild in bot.guilds:
            for role_id in data["roles"]:
                role = guild.get_role(role_id)
                if role:
                    roles.append(role)
        
        if roles:
            reaction_roles[int(message_id)] = {
                "roles": roles,
                "emojis": data["emojis"]
            }
            loaded_count += 1
    
    print(f"リアクションロールの設定を読み込みました: {loaded_count}件")
    return reaction_roles

def format_error_message(error: Exception) -> str:
    """エラーメッセージをフォーマットする"""
    error_type = type(error).__name__
    error_msg = str(error)
    tb = traceback.format_exc()
    return (
        f"❌ エラーが発生しました:\n"
        f"エラーの種類: {error_type}\n"
        f"エラーメッセージ: {error_msg}\n"
        f"```\n{tb}\n```"
    )

def get_category_by_name(guild: discord.Guild, name: str) -> Optional[discord.CategoryChannel]:
    """カテゴリを名前で取得する（絵文字の結合/分解に対応）"""
    category = discord.utils.get(guild.categories, name=name)
    if not category:
        # 絵文字が分解されている可能性がある場合の代替名
        alt_name = name.replace("👨‍", "👨").replace("👨‍", "👨")
        category = discord.utils.get(guild.categories, name=alt_name)
    return category 