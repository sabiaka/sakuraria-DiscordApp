import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv(dotenv_path='.env')

# Botの設定
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

# コマンドの設定
COMMAND_PREFIX = '!'

# 権限チェックの設定
ADMIN_CHANNEL_NAME = "botテスト場"
STAFF_ROLE_NAME = "管理者テスト"
UNASSIGNED_ROLE_NAME = "ロール未付与テスト"

# リアクションロールの設定
REACTION_ROLE_CHANNELS = {
    "staff": "職員todoリスト",  # 職員用リアクションロールのチャンネル名
    "student": "総合受付"      # 生徒用リアクションロールのチャンネル名
} 