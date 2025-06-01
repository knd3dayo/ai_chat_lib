import os
import sys
import argparse

from ai_chat_lib.cmd_tools.client_util import *

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

os.environ["PYTHONUTF8"] = "1"

def __process_arguments(sys_args: list[str]) -> argparse.Namespace:
    """
    コマンドライン引数を処理する関数
    :param sys_args: コマンドライン引数
    :return: リクエストJSONファイル, APIのURL, 出力ファイル, 処理の種類
    """
    parser = argparse.ArgumentParser(
        description="Folders API Command Line Tool",
        add_help=False
    )
    parser.add_argument("-f", dest="input_file", help="リクエストJSONファイルの指定")
    parser.add_argument("-s", dest="api_base", required=True, help="APIのBaseURL")
    parser.add_argument("-o", dest="output_file", help="出力ファイルの指定")
    parser.add_argument("operation", nargs="?", choices=["list", "update", "delete"], help="操作の種類")
    parser.add_argument("-h", "--help", action="help", help="ヘルプの表示")

    args = parser.parse_args(sys_args[1:])

    if not args.operation:
        print("Operation must be specified (list, update, delete).")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)

    if args.operation == "update" and not args.input_file:
        print("Input file must be specified with -f option for update operation.")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)
    if args.operation == "delete" and not args.input_file:
        print("Input file must be specified with -f option for delete operation.")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)
    if args.operation == "list" and args.input_file:
        print("Input file should not be specified for list operation.")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)
    if not args.api_base:
        print("API base URL must be specified with -s option.")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)
    if not args.output_file:
        print("Output file must be specified with -o option.")
        usage = parser.format_help()
        print(usage)
        sys.exit(1)
    return args


async def call_list_folders_api(api_base: str) -> dict:
    list_folders_api_endpoint = api_base + "/get_content_folders"
    response_dict = await send_request({}, list_folders_api_endpoint)
    return response_dict

async def call_update_folders_api(request_dict: dict, api_base: str) -> None:
    update_folders_api_endpoint = api_base + "/update_content_folders"
    response_dict = await send_request(request_dict, update_folders_api_endpoint)
    logger.debug(f"Response data: {response_dict}")
    folders: list[str] = response_dict.get("folders", [])
    for folder in folders:
        print(f"Folder Path: {folder}")

async def main():
    args = __process_arguments(sys.argv)

    if args.operation == "list":
        request_dict = await call_list_folders_api(args.api_base)
        print_response(request_dict.get("content_folders", []), output_file=args.output_file)
        return

    if args.operation == "update":
        if not args.input_file:
            print("Input file must be specified with -f option for update operation.")
            usage = "Usage: python folders_api.py -f <input_file> -s <api_base> -o <output_file> update"
            print(usage)
            sys.exit(1)
        request_dict = prepare_folders_request(args.input_file)
        print(f"Request dict: {request_dict}")
        await call_update_folders_api(request_dict, args.api_base)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
