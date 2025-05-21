import os
import sys
import getopt

from ai_chat_lib.cmd_tools.client_util import *

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

os.environ["PYTHONUTF8"] = "1"
def usage():
    """
    コマンドライン引数の使い方を表示する関数
    :return: None
    """
    # usage
    

def __process_arguments(sys_args: list[str]) -> tuple:
    """
    コマンドライン引数を処理する関数
    :param sys_args: コマンドライン引数
    :return: リクエストJSONファイル, APIのURL, 処理の種類
    """
    # リクエストJSONファイルの指定
    request_json_file = None
    # APIのURL
    api_base = None
    # operationの指定
    operation = None

    opts, args = getopt.getopt(sys_args[1:], "f:s:h")
    for opt, arg in opts:
        if opt == "-f":
            # リクエストJSONファイルの指定
            request_json_file = arg
        elif opt == "-s":
            # APIのURLの指定
            api_base = arg
        elif opt == "-h":
            # ヘルプの表示
            usage()
            sys.exit(0)

    # 非オプション引数の処理
    if args:
        # args[0] をoperationとして取得
        operation = args[0]
        # operationがlist,update,delete以外の場合はエラー
        if operation not in ["list", "update", "delete"]:
            print(f"Invalid operation: {operation}")
            usage()
            sys.exit(1)

    # APIのURLが指定されていない場合はエラー
    if not api_base:
        print("API base URL must be specified with -s option.")
        usage()
        sys.exit(1)

    return request_json_file, api_base, operation

async def call_list_folders_api(api_base: str) -> None:
    """
    APIを呼び出す関数
    :param api_base: APIのBaseURL
    :return: なし
    """
    # APIエンドポイント
    list_folders_api_endpoint = api_base + "/get_content_folders"

    response_dict = await send_request({}, list_folders_api_endpoint)
    # outputの取得
    logger.debug(f"Response data: {response_dict}")
    folders: list[str] = response_dict.get("folders", [])
    for folder in folders:
        print(f"Folder Path: {folder}")

async def call_update_folders_api(request_dict: dict, api_base: str) -> None:
    """
    APIを呼び出す関数
    :param request_dict: リクエスト辞書
    :param api_base: APIのBaseURL
    :return: なし
    """
    # APIエンドポイント
    update_folders_api_endpoint = api_base + "/update_content_folders"

    response_dict = await send_request(request_dict, update_folders_api_endpoint)
    # outputの取得
    logger.debug(f"Response data: {response_dict}")
    folders: list[str] = response_dict.get("folders", [])
    for folder in folders:
        print(f"Folder Path: {folder}")

async def main():

    # コマンドライン引数の処理
    request_json_file, api_base,  operation = __process_arguments(sys.argv)

    if operation == "list":
        await call_list_folders_api(api_base)
        return
    if operation == "update":


    # リクエストの準備
    request_dict = prepare_vector_search_request(request_json_file)

    # list_foldersのフラグが立っている場合はフォルダ一覧を表示する。
    if operation == "list":
        await call_list_folders_api(api_base)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())