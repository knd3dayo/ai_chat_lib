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
    # アプリケーションの初期化
    await init_app()

    if init_flag:
        # 初期化コマンドが指定された場合は、アプリケーションの初期化のみ実行して終了
        return

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