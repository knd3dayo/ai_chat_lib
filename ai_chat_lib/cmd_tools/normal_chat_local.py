import os
import sys
import asyncio
import argparse

from ai_chat_lib.cmd_tools.client_util import *
from ai_chat_lib.chat_modules import ChatUtil

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

os.environ["PYTHONUTF8"] = "1"
def __process_arguments(sys_args: list[str]):
    """
    コマンドライン引数を処理する関数
    :param sys_args: コマンドライン引数
    :return: リクエストJSONファイル, インタラクティブモードのフラグ, メッセージ, 初期化フラグ
    """
    parser = argparse.ArgumentParser(description="Normal Chat Local CLI")
    parser.add_argument("-f", "--file", dest="request_json_file", help="リクエストJSONファイルの指定")
    parser.add_argument("-d", "--data-path", dest="app_data_path", help="APP_DATA_PATHの指定")
    parser.add_argument("-i", "--interactive", action="store_true", help="インタラクティブモードの指定")
    parser.add_argument("-m", "--message", dest="message", help="メッセージの指定")
    parser.add_argument("command", nargs="?", help="コマンド (例: init)")
    args, unknown = parser.parse_known_args(sys_args[1:])
    request_json_file = args.request_json_file
    args, _ = parser.parse_known_args(sys_args[1:])
    request_json_file = args.request_json_file
    interactive_mode = args.interactive
    message = args.message
    init_flag = args.command == "init" if args.command else False
    return request_json_file, interactive_mode, message, init_flag


def init_app() -> None:
    """
    アプリケーション初期化時に呼び出される関数
    :return: None
    """
    # MainDBの初期化
    from ai_chat_lib.db_modules import MainDBUtil
    MainDBUtil.init()
    print("MainDB initialized.")

def check_app_data_path():
    """
    環境変数APP_DATA_PATHが設定されているか確認する関数
    :return: APP_DATA_PATHの値
    """
    if not os.environ.get("APP_DATA_PATH", None):
        # 環境変数APP_DATA_PATHが指定されていない場合はエラー. APP_DATA_PATHの説明を出力するとともに終了する
        logger.error("APP_DATA_PATH is not set.")
        logger.error("APP_DATA_PATH is the path to the root directory where the application data is stored.")
        raise ValueError("APP_DATA_PATH is not set.")

async def run_chat_async(request_dict: dict ):
    """
    非同期でチャットを実行する関数
    :param request_dict: リクエスト辞書
    :return: レスポンス辞書
    """
    # run_openai_chat_async_apiを実行
    response_dict = await ChatUtil.run_openai_chat_async_api(request_dict)
    output:str = response_dict.get("output", "")
    if output:
        print(output)
    else:
        print("No output found in the response.")

async def run_chat_interactive_async(request_dict: dict) -> None:
    """
    インタラクティブモードでチャットを実行する関数
    :param request_dict: リクエスト辞書
    :return: None
    """
    # インタラクティブモードでチャットを実行
    while True:
        input_message = input("User: ")
        # ユーザーメッセージを追加
        add_normal_chat_message("user", input_message, request_dict)
        response_dict = await ChatUtil.run_openai_chat_async_api(request_dict)
        # レスポンスを取得
        output = response_dict.get("output")
        if output:
            print(f"Assistant:\n{output}")
            # レスポンスを追加
            add_normal_chat_message("assistant", output, request_dict)
        else:
            print("No output found in the response.")

    
async def main():
    
    # argparseによるコマンドライン引数の処理
    request_json_file, interactive_mode, message, init_flag = __process_arguments(sys.argv)
    if init_flag:
        # アプリケーションの初期化
        init_app()
        return

    # 環境変数APP_DATA_PATHの確認
    check_app_data_path() 

    # リクエストの準備
    request_dict = prepare_normal_chat_request(request_json_file, interactive_mode, message)

    # run_openai_chat_async_apiを実行
    if interactive_mode:
        # インタラクティブモードでチャットを実行
        await run_chat_interactive_async(request_dict)
    else:
        # 非同期でチャットを実行
        await run_chat_async(request_dict)

if __name__ == '__main__':
    asyncio.run(main())