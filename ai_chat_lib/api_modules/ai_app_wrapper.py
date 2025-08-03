"""
ai_app_wrapper.py

APIサーバの各種エンドポイントに対応するラッパー関数群を提供するモジュール。
- DB/プロセス/プロンプト/ベクトルDB/タグ/ファイル/外部API等の管理・操作APIを一括でラップ
- 各関数はAPIサーバのルーティングから呼び出される
"""

import os, json

from ai_chat_lib.api_modules.ai_app_util import *
from ai_chat_lib.langchain_modules.langchain_util import  LangChainUtil
from ai_chat_lib.file_modules.excel_util import ExcelUtil
from ai_chat_lib.file_modules.file_util import FileUtil
from ai_chat_lib.web_modules.web_util import WebUtil
from ai_chat_lib.chat_modules.chat_util import ChatUtil
from ai_chat_lib.db_modules.search_rule import SearchRule
from ai_chat_lib.db_modules.auto_process_item import AutoProcessItem
from ai_chat_lib.db_modules.auto_process_rule import AutoProcessRule
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from ai_chat_lib.db_modules.content_item import ContentItem

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
    return await ContentItem.get_content_items_by_folder_id_api(request_json)

@capture_stdout_stderr_async
async def get_content_item_by_id(request_json: str):
    """
    ContentItemのID指定取得APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: ContentItem情報
    """
    return await ContentItem.get_content_item_by_id_api(request_json)

@capture_stdout_stderr_async
async def update_content_items(request_json: str):  
    """
    ContentItemの更新APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 更新結果
    """
    return await ContentItem.update_content_items_api(request_json)
@capture_stdout_stderr_async
async def delete_content_items(request_json: str):
    """
    ContentItemの削除APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 削除結果
    """
    return await ContentItem.delete_content_items_api(request_json)

@capture_stdout_stderr_async
async def search_content_items(request_json: str):
    """
    ContentItemの検索APIラッパー。

    Args:
        request_json (str): リクエストパラメータ(JSON文字列)
    Returns:
        dict: 検索結果
    """
    return await ContentItem.search_content_items_api(request_json)

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
    return await SearchRule.get_search_rules_api(request_json)
@capture_stdout_stderr_async
async def update_search_rules(request_json: str):
    return await SearchRule.update_search_rules_api(request_json)
@capture_stdout_stderr_async
async def delete_search_rules(request_json: str):
    return await SearchRule.delete_search_rules_api(request_json)

########################
# AutoProcessItem関連
########################
@capture_stdout_stderr_async
async def get_auto_process_items(request_json: str):
    return await AutoProcessItem.get_auto_process_items_api(request_json)
@capture_stdout_stderr_async
async def update_auto_process_items(request_json: str):
    return await AutoProcessItem.update_auto_process_items_api(request_json)
@capture_stdout_stderr_async
async def delete_auto_process_items(request_json: str):
    return await AutoProcessItem.delete_auto_process_items_api(request_json)

########################
# AutoProcessRule関連
########################
@capture_stdout_stderr_async
async def get_auto_process_rules(request_json: str):
    return await AutoProcessRule.get_auto_process_rules_api(request_json)
@capture_stdout_stderr_async
async def update_auto_process_rules(request_json: str):
    return await AutoProcessRule.update_auto_process_rules_api(request_json)
@capture_stdout_stderr_async
async def delete_auto_process_rules(request_json: str):
    return await AutoProcessRule.delete_auto_process_rules_api(request_json)

########################
# PromptItem関連
########################
@capture_stdout_stderr_async
async def get_prompt_items(request_json: str):
    return await PromptItem.get_prommt_items_api()
@capture_stdout_stderr_async
async def get_prompt_item(request_json: str):
    return await PromptItem.get_prompt_item_api(request_json)
@capture_stdout_stderr_async
async def update_prompt_items(request_json: str):
    return await PromptItem.update_prompt_items_api(request_json)
@capture_stdout_stderr_async
async def delete_prompt_items(request_json: str):
    return await PromptItem.delete_prompt_items_api(request_json)

########################
# ContentFolders関連
########################
@capture_stdout_stderr_async
async def get_root_content_folders():
    return await ContentFolder.get_root_content_folders_api()
@capture_stdout_stderr_async
async def get_content_folders():
    return await ContentFolder.get_content_folders_api()
@capture_stdout_stderr_async
async def get_content_folder_by_id(request_json: str):
    return await ContentFolder.get_content_folder_by_id_api(request_json)
@capture_stdout_stderr_async
async def get_content_folder_by_path(request_json: str):
    return await ContentFolder.get_content_folder_by_path_api(request_json)
@capture_stdout_stderr_async
async def get_parent_content_folder_by_id(request_json: str):
    return await ContentFolder.get_parent_content_folder_by_id_api(request_json)
@capture_stdout_stderr_async
async def get_child_content_folders_by_id(request_json: str):
    return await ContentFolder.get_child_content_folders_by_id_api(request_json)
@capture_stdout_stderr_async
async def update_content_folders(request_json: str):
    return await ContentFolder.update_content_folders_api(request_json)
@capture_stdout_stderr_async
async def delete_content_folders(request_json: str):
    return await ContentFolder.delete_content_folders_api(request_json)

########################
# tag関連
########################
@capture_stdout_stderr_async
async def get_tag_items(request_json: str):
    return await TagItem.get_tag_items_api(request_json)

@capture_stdout_stderr_async
async def update_tag_items(request_json: str):
    return await TagItem.update_tag_items_api(request_json)

@capture_stdout_stderr_async
async def delete_tag_items(request_json: str):
    return await TagItem.delete_tag_items_api(request_json)

########################
# openai関連
########################
@capture_stdout_stderr_async
async def openai_chat_async(request_dict: dict) -> dict:
    return await ChatUtil.run_openai_chat_async_api(request_dict)

@capture_stdout_stderr
def get_token_count(request_json: str):
    return ChatUtil.get_token_count_api(request_json)

########################
# ベクトルDB関連
########################
# vector_db_itemを更新する
@capture_stdout_stderr_async
async def update_vector_db(request_json: str):
    return await VectorDBItem.update_vector_db_api(request_json)

# vector_db_itemを削除する
@capture_stdout_stderr_async
async def delete_vector_db(request_json: str):
    return await VectorDBItem.delete_vector_db_api(request_json)

# vector_dbのリストを取得する
@capture_stdout_stderr_async
async def get_vector_db_items():
    return await VectorDBItem.get_vector_db_items_api()

# get_vector_db_item_by_idを実行する
@capture_stdout_stderr_async
async def get_vector_db_item_by_id(request_json: str):
    return await VectorDBItem.get_vector_db_item_by_id_api(request_json)

# get_vector_db_item_by_nameを実行する
@capture_stdout_stderr_async
async def get_vector_db_item_by_name(request_json: str):
    return await VectorDBItem.get_vector_db_item_by_name_api(request_json)

@capture_stdout_stderr_async
async def vector_search(request_json: str):
    return await LangChainUtil.vector_search_api(request_json)

@capture_stdout_stderr
def update_collection(request_json: str):
    return LangChainUtil.update_collection_api(request_json)

@capture_stdout_stderr_async
async def delete_collection(request_json: str):
    return await LangChainUtil.delete_collection_api(request_json)

# ベクトルDBのインデックスをフォルダ単位で削除する
@capture_stdout_stderr_async
async def delete_embeddings_by_folder(request_json: str):
    return await LangChainUtil.delete_embeddings_by_folder_api(request_json)

# ベクトルDBのインデックスを削除する
@capture_stdout_stderr_async
async def delete_embeddings(request_json: str):
    return await LangChainUtil.delete_embeddings_api(request_json)

# ベクトルDBのコンテンツインデックスを更新する
@capture_stdout_stderr_async
async def update_embeddings(request_json: str) -> dict:
    return await LangChainUtil.update_embeddings_api(request_json)

########################
# ファイル関連
########################
# ファイルのMimeTypeを取得する
@capture_stdout_stderr
def get_mime_type(request_json: str):
    return FileUtil.get_mime_type_api(request_json)

# Excelのシート名一覧を取得する
@capture_stdout_stderr
def get_sheet_names(request_json: str):
    return ExcelUtil.get_sheet_names_api(request_json)

# Excelのシートのデータを取得する
@capture_stdout_stderr
def extract_excel_sheet(request_json: str):
    return ExcelUtil.extract_excel_sheet_api(request_json)

# ファイルからテキストを抽出する
@capture_stdout_stderr_async
async def extract_text_from_file_async(request_json: str) -> dict:
    return await FileUtil.extract_text_from_file_async_api(request_json)

# base64形式のデータからテキストを抽出する
@capture_stdout_stderr_async
async def extract_base64_to_text_async(request_json: str):
    return await FileUtil.extract_base64_to_text_async_api(request_json)

@capture_stdout_stderr_async
async def extract_webpage(request_json: str):
    return await WebUtil.extract_webpage_api(request_json)

# export_to_excelを実行する
@capture_stdout_stderr
def export_to_excel(request_json: str):
    return ExcelUtil.export_to_excel_api(request_json)

# import_from_excelを実行する
@capture_stdout_stderr
def import_from_excel(request_json: str):
    return ExcelUtil.import_from_excel_api(request_json)

# テスト用
def hello_world():
    return {"output": "Hello, World!"}
