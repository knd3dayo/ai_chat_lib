"""
5秒ごとに指定したプロセスID（pid）を監視し、
プロセスが存在しなくなった場合に指定URLへPOSTリクエストを送信するユーティリティ。
主にメインアプリ終了時にFlaskサーバーを安全に停止する用途で利用する。
"""

import sys, os
import time
import requests # type: ignore
import psutil # type: ignore

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)


def check_process(pid: int, url: str):
    """
    指定したプロセスID（pid）を5秒ごとに監視し、
    プロセスが存在しなくなった場合に指定URLへPOSTリクエストを送信する。

    Args:
        pid (int): 監視対象のプロセスID
        url (str): プロセス終了時にリクエストを送信するURL
    """
    while True:
        time.sleep(5)
        # pidのプロセスが存在しない場合
        if not psutil.pid_exists(pid):
            # 指定したURLにリクエストを送信
            try:
                os.environ["NO_PROXY"] = "localhost"
                # エラーを無視してリクエストを送信 timeout=5
                requests.post(url, timeout=5)
            except Exception:
                pass

            break

# メイン
if __name__ == "__main__":
    # 引数の取得
    args = sys.argv
    if len(args) != 3:
        print("Usage: python ai_app_process_checker.py [pid] [url]")
        sys.exit(1)
    pid = int(args[1])
    url = args[2]

    # プロセスを監視
    check_process(pid, url)
