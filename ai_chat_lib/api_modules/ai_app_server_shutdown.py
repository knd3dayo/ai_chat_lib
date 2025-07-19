"""
ai_app_server_shutdown.py

メインアプリのプロセス終了時にFlaskサーバーを安全に停止するためのユーティリティ。
指定したURLにPOSTリクエストを送信し、サーバーシャットダウンをトリガーする用途で利用する。
"""

import sys, os
import requests # type: ignore

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

def stop_process(url: str):
    """
    指定したURLにPOSTリクエストを送信し、Flaskサーバーのシャットダウンをトリガーする。

    Args:
        url (str): サーバー停止リクエストを送信するURL
    """
    try:
        os.environ["NO_PROXY"] = "localhost"
        # エラーを無視してリクエストを送信 timeout=60
        requests.post(url, timeout=60)
    except Exception as e:
        import traceback
        logger.error(traceback.format_exc())
        logger.error("Failed to send a request to the specified URL")

# メイン
if __name__ == "__main__":
    # 引数の取得
    args = sys.argv
    if len(args) != 2:
        print("Usage: python ai_app_process_checker.py [url]")
        sys.exit(1)
    url = args[1]
    # サーバー停止リクエストを送信
    stop_process(url)
