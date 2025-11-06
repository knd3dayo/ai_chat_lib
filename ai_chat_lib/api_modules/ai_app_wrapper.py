"""
ai_app_wrapper.py

APIサーバの各種エンドポイントに対応するラッパー関数群を提供するモジュール。
- DB/プロセス/プロンプト/ベクトルDB/タグ/ファイル/外部API等の管理・操作APIを一括でラップ
- 各関数はAPIサーバのルーティングから呼び出される
"""

import os, json

from ai_chat_lib.api_modules.ai_app_util import *
from ai_chat_lib.api_modules.ai_app_chat_modules import LangChainUtilAPI, ChatUtilAPI
from ai_chat_lib.api_modules.ai_app_file_modules import FileUtilAPI, ExcelUtilAPI
from ai_chat_lib.api_modules.ai_app_web_modules import WebUtilAPI
from ai_chat_lib.api_modules.ai_app_db_modules import *

from ai_chat_mcp.chat.chat_util import CompletionResponse

# Proxy環境下でのSSLエラー対策。HTTPS_PROXYが設定されていない場合はNO_PROXYを設定する
if "HTTPS_PROXY" not in os.environ:
    os.environ["NO_PROXY"] = "*"
# AutoGenのCodeExecutor実行時にUncicodeEncodeErrorが発生するため、Pythonのデフォルトの文字コードをUTF-8に設定
os.environ["PYTHONUTF8"] = "1"
########################
# ContentItem関連
########################
@capture_stdout_stderr_async
async def get_content_items(request_json: str):
    """
    ContentItemの取得APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: ContentItem情報
    """
    return await ContentItem.get_content_items_api()

@capture_stdout_stderr_async
async def get_content_items_by_folder_id(request_json: str):
    """
    ContentItemのフォルダID指定取得APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: ContentItem情報
    """
    return await ContentItemAPI.get_content_items_by_folder_id_api(request_json)

@capture_stdout_stderr_async
async def get_content_item_by_id(request_json: str):
    """
    ContentItemのID指定取得APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: ContentItem情報
    """
    return await ContentItemAPI.get_content_item_by_id_api(request_json)

@capture_stdout_stderr_async
async def update_content_items(request_json: str):  
    """
    ContentItemの更新APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 更新結果
    """
    return await ContentItemAPI.update_content_items_api(request_json)
@capture_stdout_stderr_async
async def delete_content_items(request_json: str):
    """
    ContentItemの削除APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 削除結果
    """
    return await ContentItemAPI.delete_content_items_api(request_json)

@capture_stdout_stderr_async
async def search_content_items(request_json: str):
    """
    ContentItemの検索APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 検索結果
    """
    return await ContentItemAPI.search_content_items_api(request_json)

########################
# SearchRule関連
########################
@capture_stdout_stderr_async
async def get_search_rules(request_json: str):
    """
    SearchRuleの取得APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 検索ルール情報
    """
    return await SearchRuleAPI.get_search_rules_api(request_json)
@capture_stdout_stderr_async
async def update_search_rules(request_json: str):
    return await SearchRuleAPI.update_search_rules_api(request_json)
@capture_stdout_stderr_async
async def delete_search_rules(request_json: str):
    return await SearchRuleAPI.delete_search_rules_api(request_json)

########################
# AutoProcessItem関連
########################
@capture_stdout_stderr_async
async def get_auto_process_items(request_json: str):
    return await AutoProcessItemAPI.get_auto_process_items_api(request_json)
@capture_stdout_stderr_async
async def update_auto_process_items(request_json: str):
    return await AutoProcessItemAPI.update_auto_process_items_api(request_json)
@capture_stdout_stderr_async
async def delete_auto_process_items(request_json: str):
    return await AutoProcessItemAPI.delete_auto_process_items_api(request_json)

########################
# AutoProcessRule関連
########################
@capture_stdout_stderr_async
async def get_auto_process_rules(request_json: str):
    return await AutoProcessRuleAPI.get_auto_process_rules_api(request_json)
@capture_stdout_stderr_async
async def update_auto_process_rules(request_json: str):
    return await AutoProcessRuleAPI.update_auto_process_rules_api(request_json)
@capture_stdout_stderr_async
async def delete_auto_process_rules(request_json: str):
    return await AutoProcessRuleAPI.delete_auto_process_rules_api(request_json)

########################
# PromptItem関連
########################
@capture_stdout_stderr_async
async def get_prompt_items(request_json: str):
    return await PromptItemAPI.get_prommt_items_api()
@capture_stdout_stderr_async
async def get_prompt_item(request_json: str):
    return await PromptItemAPI.get_prompt_item_api(request_json)
@capture_stdout_stderr_async
async def update_prompt_items(request_json: str):
    return await PromptItemAPI.update_prompt_items_api(request_json)
@capture_stdout_stderr_async
async def delete_prompt_items(request_json: str):
    return await PromptItemAPI.delete_prompt_items_api(request_json)

########################
# ContentFolders関連
########################
@capture_stdout_stderr_async
async def get_root_content_folders():
    return await ContentFolderAPI.get_root_content_folders_api()
@capture_stdout_stderr_async
async def get_content_folders():
    return await ContentFolderAPI.get_content_folders_api()
@capture_stdout_stderr_async
async def get_content_folder_by_id(request_json: str):
    return await ContentFolderAPI.get_content_folder_by_id_api(request_json)
@capture_stdout_stderr_async
async def get_content_folder_by_path(request_json: str):
    return await ContentFolderAPI.get_content_folder_by_path_api(request_json)
@capture_stdout_stderr_async
async def get_parent_content_folder_by_id(request_json: str):
    return await ContentFolderAPI.get_parent_content_folder_by_id_api(request_json)
@capture_stdout_stderr_async
async def get_child_content_folders_by_id(request_json: str):
    return await ContentFolderAPI.get_child_content_folders_by_id_api(request_json)
@capture_stdout_stderr_async
async def update_content_folders(request_json: str):
    return await ContentFolderAPI.update_content_folders_api(request_json)
@capture_stdout_stderr_async
async def delete_content_folders(request_json: str):
    return await ContentFolderAPI.delete_content_folders_api(request_json)

########################
# tag関連
########################
@capture_stdout_stderr_async
async def get_tag_items(request_json: str):
    return await TagItemAPI.get_tag_items_api(request_json)

@capture_stdout_stderr_async
async def update_tag_items(request_json: str):
    return await TagItemAPI.update_tag_items_api(request_json)

@capture_stdout_stderr_async
async def delete_tag_items(request_json: str):
    return await TagItemAPI.delete_tag_items_api(request_json)

########################
# openai関連
########################
@capture_stdout_stderr_async
async def openai_chat_async(request_dict: dict) -> dict:
    chat_output: CompletionResponse = await ChatUtilAPI.run_openai_chat_async_api(request_dict)
    return chat_output.model_dump()

@capture_stdout_stderr
def get_token_count(request_json: str):
    return ChatUtilAPI.get_token_count_api(request_json)

########################
# ベクトルDB関連
########################
# vector_db_itemを更新する
@capture_stdout_stderr_async
async def update_vector_db(request_json: str):
    return await VectorDBItemAPI.update_vector_db_api(request_json)

# vector_db_itemを削除する
@capture_stdout_stderr_async
async def delete_vector_db(request_json: str):
    return await VectorDBItemAPI.delete_vector_db_api(request_json)

# vector_dbのリストを取得する
@capture_stdout_stderr_async
async def get_vector_db_items():
    return await VectorDBItemAPI.get_vector_db_items_api()

# get_vector_db_item_by_idを実行する
@capture_stdout_stderr_async
async def get_vector_db_item_by_id(request_json: str):
    return await VectorDBItemAPI.get_vector_db_item_by_id_api(request_json)

# get_vector_db_item_by_nameを実行する
@capture_stdout_stderr_async
async def get_vector_db_item_by_name(request_json: str):
    return await VectorDBItemAPI.get_vector_db_item_by_name_api(request_json)

@capture_stdout_stderr_async
async def vector_search(request_json: str):
    return await LangChainUtilAPI.vector_search_api(request_json)

@capture_stdout_stderr
def update_collection(request_json: str):
    return LangChainUtilAPI.update_collection_api(request_json)

@capture_stdout_stderr_async
async def delete_collection(request_json: str):
    return await LangChainUtilAPI.delete_collection_api(request_json)

# ベクトルDBのインデックスをフォルダ単位で削除する
@capture_stdout_stderr_async
async def delete_embeddings_by_folder(request_json: str):
    return await LangChainUtilAPI.delete_embeddings_by_folder_api(request_json)

# ベクトルDBのインデックスを削除する
@capture_stdout_stderr_async
async def delete_embeddings(request_json: str):
    return await LangChainUtilAPI.delete_embeddings_api(request_json)

# ベクトルDBのコンテンツインデックスを更新する
@capture_stdout_stderr_async
async def update_embeddings(request_json: str) -> dict:
    return await LangChainUtilAPI.update_embeddings_api(request_json)

########################
# ファイル関連
########################
# ファイルのMimeTypeを取得する
@capture_stdout_stderr
def get_mime_type(request_json: str):
    return FileUtilAPI.get_mime_type_api(request_json)

# Excelのシート名一覧を取得する
@capture_stdout_stderr
def get_sheet_names(request_json: str):
    return ExcelUtilAPI.get_sheet_names_api(request_json)

# Excelのシートのデータを取得する
@capture_stdout_stderr
def extract_excel_sheet(request_json: str):
    return ExcelUtilAPI.extract_excel_sheet_api(request_json)

# ファイルからテキストを抽出する
@capture_stdout_stderr_async
async def extract_text_from_file_async(request_json: str) -> dict:
    return await FileUtilAPI.extract_text_from_file_async_api(request_json)

# base64形式のデータからテキストを抽出する
@capture_stdout_stderr_async
async def extract_base64_to_text_async(request_json: str):
    return await FileUtilAPI.extract_base64_to_text_async_api(request_json)

@capture_stdout_stderr_async
async def extract_webpage(request_json: str):
    return await WebUtilAPI.extract_webpage_api(request_json)

# export_to_excelを実行する
@capture_stdout_stderr
def export_to_excel(request_json: str):
    return ExcelUtilAPI.export_to_excel_api(request_json)

# import_from_excelを実行する
@capture_stdout_stderr
def import_from_excel(request_json: str):
    return ExcelUtilAPI.import_from_excel_api(request_json)

# テスト用
def hello_world() -> str:
    result = {"output": "Hello, World!"}
    return json.dumps(result, ensure_ascii=False)
