import os
import sys
import argparse
import httpx  # type: ignore

from ai_chat_lib.cmd_tools.client_util import *

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

os.environ["PYTHONUTF8"] = "1"

def __process_arguments(sys_args: list[str]) -> argparse.Namespace:
    """
    argparseを使ってコマンドライン引数を処理する関数
    :param sys_args: コマンドライン引数
    :return: リクエストJSONファイル, APIのURL, メッセージ, インタラクティブモードのフラグ
    """
    parser = argparse.ArgumentParser(
        description="Normal Chat API Client",
        add_help=False
    )
    parser.add_argument("-f", dest="request_json_file", required=True, help="リクエストJSONファイル")
    parser.add_argument("-s", dest="api_base", help="APIのURL")
    parser.add_argument("-i", dest="interactive_mode", action="store_true", help="インタラクティブモード")
    parser.add_argument("-m", dest="message", help="メッセージ")
    parser.add_argument("-h", "--help", action="help", help="ヘルプ")

    args = parser.parse_args(sys_args[1:])
    if not args.request_json_file:
        usage = parser.format_help()
        print(usage)
        raise ValueError("リクエストJSONファイルを指定してください。")
    
    if not args.api_base:
        usage = parser.format_help()
        print(usage)
        raise ValueError("APIのURLを指定してください。")
    if not args.message:
        args.message = "Hello, how can I help you today?"
    if args.interactive_mode and not args.message:
        usage = parser.format_help()
        print(usage)
        raise ValueError("インタラクティブモードではメッセージを指定できません。")
    return args

async def call_api(request_dict: dict, api_endpoint: str):
    response_dict = await send_request(request_dict, api_endpoint)
    output = response_dict.get("output")
    if output:
        print(output)
    else:
        raise ValueError("No output found in the response.")

async def call_api_interactve(request_dict: dict, api_endpoint: str):
    while True:
        input_message = input("User: ")
        add_normal_chat_message("user", input_message, request_dict)
        response_dict = await send_request(request_dict, api_endpoint)
        output = response_dict.get("output")
        if output:
            print(f"Assistant:\n{output}")
            add_normal_chat_message("assistant", output, request_dict)
        else:
            print("No output found in the response.")

async def main():
    args = __process_arguments(sys.argv)
    request_dict = prepare_normal_chat_request(args.request_json_file, args.interactive_mode, args.message)
    api_endpoint = args.api_base + "/openai_chat"
    if args.interactive_mode:
        await call_api_interactve(request_dict, api_endpoint)
    else:
        await call_api(request_dict, api_endpoint)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
