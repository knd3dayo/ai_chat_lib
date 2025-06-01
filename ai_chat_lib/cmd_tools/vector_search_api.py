import os
import sys
import argparse

from ai_chat_lib.cmd_tools.client_util import *

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

os.environ["PYTHONUTF8"] = "1"

def __process_arguments(sys_args: list[str]) -> tuple:
    """
    コマンドライン引数を処理する関数 (argparse版)
    :param sys_args: コマンドライン引数
    :return: リクエストJSONファイル, APIのURL,  メッセージ, 検索結果数, スコア閾値, ベクトルDBの検索対象フォルダ
    """
    parser = argparse.ArgumentParser(
        description="Vector Search API Client",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-f", "--request_json_file", type=str, help="リクエストJSONファイル")
    parser.add_argument("-s", "--api_base", type=str, required=True, help="APIのURL")
    parser.add_argument("-m", "--message", type=str, help="メッセージ")
    parser.add_argument("-k", "--search_result_count", type=int, default=10, help="検索結果の数 (default: 10)")
    parser.add_argument("-t", "--score_threshold", type=float, default=0.5, help="スコアの閾値 (default: 0.5)")
    parser.add_argument("-p", "--vector_db_folder", type=str, help="ベクトルDBの検索対象フォルダ")

    args = parser.parse_args(sys_args[1:])

    if args.search_result_count <= 0:
        parser.error("Search result count must be greater than 0.")
    if args.score_threshold < 0.0 or args.score_threshold > 1.0:
        parser.error("Score threshold must be between 0.0 and 1.0.")
    if not args.request_json_file and not args.message:
        parser.error("Either request_json_file or message must be specified.")

    return (
        args.request_json_file,
        args.api_base,
        args.message,
        args.search_result_count,
        args.score_threshold,
        args.vector_db_folder
    )

async def call_vector_search_api(request_dict: dict, api_base: str) -> None:
    """
    APIを呼び出す関数
    :param request_dict: リクエスト辞書
    :param api_base: APIのBaseURL
    :return: なし
    """
    vector_search_api_endpoint = api_base + "/vector_search"
    response_dict = await send_request(request_dict, vector_search_api_endpoint)
    logger.debug(f"Response data: {response_dict}")
    documents: list[dict] = response_dict.get("documents", [])
    for document in documents:
        print("--------------------------------------------------")
        print(f"Document ID: {document['doc_id']}")
        print(f"Document Score: {document['score']}")
        print(f"Document Folder Path: {document['folder_path']}")
        print(f"Document Source Path: {document.get('source_path', 'N/A')}")
        print(f"Document Content: {document['content']}")

async def main():
    request_json_file, api_base, message, search_result_count, score_threshold, vector_db_folder = __process_arguments(sys.argv)
    request_dict = prepare_vector_search_request(request_json_file, message, search_result_count, score_threshold, vector_db_folder)
    await call_vector_search_api(request_dict, api_base)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
