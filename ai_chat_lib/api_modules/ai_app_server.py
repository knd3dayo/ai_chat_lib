"""
ai_app_server.py

AIチャットアプリケーションのAPIサーバ本体。
- Aiohttp + SocketIOによる非同期APIサーバ
- 各種DB/プロセス/プロンプト/ベクトルDB/タグ等の管理APIを提供
- サーバ起動(main)・シャットダウン・セッション管理も含む
"""

from typing import Sequence
import os, sys
from fastapi import FastAPI
import uvicorn

from langchain_core.documents import Document

from ai_chat_lib.db_modules.main_db_util import MainDBUtil

from ai_chat_lib.db_modules.content_item import ContentItem
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.auto_process_item import AutoProcessItem
from ai_chat_lib.db_modules.auto_process_rule import AutoProcessRule
from ai_chat_lib.db_modules.search_rule import SearchRule
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_util.model import ChatResponse, ChatHistory, ChatRequestContext, ChatMessage
from ai_chat_util.llm.llm_client import LLMClient
from ai_chat_util.llm.llm_config import LLMConfig
from vector_search_util.model.models import EmbeddingData, VectorSearchRequest, VectorDBItemBase

from ai_chat_lib.api_modules.misc import *

from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
import ai_chat_lib.model as model_base

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()

########################
# ContentItem関連
########################
@app.get('/api/get_content_items')
async def get_content_items() -> Sequence[model_base.ContentItemModel]:

    content_items = await ContentItem.get_content_items()
    return content_items

@app.get('/api/get_content_items_by_folder_id')
async def get_content_items_by_folder_id(folder_id: str) -> Sequence[model_base.ContentItemModel]:
    content_items = await ContentItem.get_content_items_by_folder_id(folder_id)
    logger.debug(content_items)
    return content_items

@app.get('/api/get_content_item_by_id')
async def get_content_item_by_id(item_id: str) -> model_base.ContentItemModel | None:
    content_item = await ContentItem.get_content_item_by_id(item_id)
    logger.debug(content_item)
    return content_item


@app.post('/api/update_content_items')
async def update_content_items(content_items: Sequence[model_base.ContentItemModel]) -> Sequence[model_base.ContentItemModel]:
    response = await ContentItem.update_content_items(content_items)
    return response

@app.delete('/api/delete_content_items')
async def delete_content_items(items: Sequence[model_base.ContentItemModel]) -> None:
    response = await ContentItem.delete_content_items(items)
    return response

########################
# ContentFolders関連
########################
@app.get('/api/get_root_content_folders')
async def get_root_content_folders() -> Sequence[model_base.ContentFolderModel]:
    response = await ContentFolder.get_root_content_folders()
    return response

@app.get('/api/get_content_folders')
async def get_content_folders() -> Sequence[model_base.ContentFolderModel]:
    response = await ContentFolder.get_content_folders()
    return response
    
@app.get('/api/get_content_folder_by_id')
async def get_content_folder_by_id(folder_id: str) -> model_base.ContentFolderModel | None:
    content_folder = await ContentFolder.get_content_folder_by_id(folder_id)
    return content_folder

@app.get('/api/get_content_folder_by_path')
async def get_content_folder_by_path(folder_path: str) -> model_base.ContentFolderModel | None:
    content_folder = await ContentFolder.get_content_folder_by_path(folder_path)
    return content_folder

@app.get('/api/get_content_folder_path_by_id')
async def get_content_folder_path_by_id(folder_id: str) -> str | None:
    content_folder_path = await ContentFolder.get_content_folder_path_by_id(folder_id)
    return content_folder_path

@app.get('/api/get_parent_content_folder_by_id')
async def get_parent_content_folder_by_id(folder_id: str) -> model_base.ContentFolderModel | None:
    parent_content_folder = await ContentFolder.get_parent_content_folder_by_id(folder_id)
    return parent_content_folder

@app.get('/api/get_child_content_folders_by_id')
async def get_child_content_folders_by_id(folder_id: str) -> Sequence[model_base.ContentFolderModel]:
    child_content_folders = await ContentFolder.get_child_content_folders_by_id(folder_id)
    return child_content_folders

@app.post('/api/update_content_folders')
async def update_content_folders(folders: Sequence[model_base.ContentFolderModel]) -> Sequence[model_base.ContentFolderModel]:
    response = await ContentFolder.update_content_folders(folders)
    return response

@app.delete('/api/delete_content_folders')
async def delete_content_folders(folders: Sequence[model_base.ContentFolderModel]) -> Sequence[model_base.ContentFolderModel]:
    response = await ContentFolder.delete_content_folders(folders)
    return response

########################
# AutoProcessItem関連
########################
@app.get('/api/get_auto_process_items')
async def get_auto_process_items() -> Sequence[model_base.AutoProcessItemModel]:
    response = await AutoProcessItem.get_auto_process_items()
    return response

@app.post('/api/update_auto_process_items')
async def update_auto_process_items(items: Sequence[model_base.AutoProcessItemModel]) -> Sequence[model_base.AutoProcessItemModel]:
    response = await AutoProcessItem.update_auto_process_items(items)
    return response

@app.delete('/api/delete_auto_process_items')
async def delete_auto_process_items(items: Sequence[model_base.AutoProcessItemModel]) -> None:
    response = await AutoProcessItem.delete_auto_process_items(items)
    return response

########################
# AutoProcessRule関連
########################
@app.get('/api/get_auto_process_rules')
async def get_auto_process_rules() -> Sequence[model_base.AutoProcessRuleModel]:
    response = await AutoProcessRule.get_auto_process_rules()
    return response

@app.post('/api/update_auto_process_rules')
async def update_auto_process_rules(rules: Sequence[model_base.AutoProcessRuleModel]) -> Sequence[model_base.AutoProcessRuleModel]:
    response = await AutoProcessRule.update_auto_process_rules(rules)
    return response

@app.delete('/api/delete_auto_process_rules')
async def delete_auto_process_rules(rules: Sequence[model_base.AutoProcessRuleModel]) -> None:
    response = await AutoProcessRule.delete_auto_process_rules(rules)
    return response

########################
# SearchRule関連
########################
@app.get('/api/get_search_rules')
async def get_search_rules() -> Sequence[model_base.SearchRuleModel]:
    response = await SearchRule.get_search_rules()
    return response

@app.post('/api/update_search_rules')
async def update_search_rules(rules: Sequence[model_base.SearchRuleModel]) -> Sequence[model_base.SearchRuleModel]:
    response = await SearchRule.update_search_rules(rules)
    return response

@app.delete('/api/delete_search_rules')
async def delete_search_rules(rules: Sequence[model_base.SearchRuleModel]) -> None:
    response = await SearchRule.delete_search_rules(rules)
    return response

########################
# PromptItem関連
########################
@app.get('/api/get_prompt_items')
async def get_prompt_items() -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.get_prompt_items()
    return response

@app.get('/api/get_prompt_item_by_id')
async def get_prompt_item(item_id: str) -> model_base.PromptItemModel | None:
    response = await PromptItem.get_prompt_item_by_id(item_id)
    return response

@app.post('/api/update_prompt_items')
async def update_prompt_items(items: Sequence[model_base.PromptItemModel]) -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.update_prompt_items(items)
    return response

@app.delete('/api/delete_prompt_items')
async def delete_prompt_items(items: Sequence[model_base.PromptItemModel]) -> None:
    response = await PromptItem.delete_prompt_items(items)
    return response

########################
# Tag関連
########################
@app.get('/api/get_tag_items')
async def get_tag_items() -> Sequence[model_base.TagItemModel]:
    response = await TagItem.get_tag_items()
    return response

@app.post('/api/update_tag_items')
async def update_tag_items(items: Sequence[model_base.TagItemModel]) -> Sequence[model_base.TagItemModel]:
    response = await TagItem.update_tag_items(items)
    return response

@app.delete('/api/delete_tag_items')
async def delete_tag_items(items: Sequence[model_base.TagItemModel]) -> None:
    response = await TagItem.delete_tag_items(items)
    return response

########################
# OpenAI Chat関連
########################
@app.post('/api/openai_chat')
async def openai_chat(request: ChatMessage, chat_history: ChatHistory, context: ChatRequestContext) -> ChatResponse:
    client = LLMClient.create_llm_client(LLMConfig(), chat_history=chat_history, request_context=context)
    response = await client.run_chat(request)
    return response

@app.get('/api/get_token_count')
async def get_token_count(model: str, text: str) -> int:
    response = LLMClient.get_token_count(model, text)
    return response

########################
# ベクトルDB関連
########################

# get_vector_db_items
@app.get('/api/get_vector_db_items')
async def get_vector_db_items() -> Sequence[VectorDBItemBase]:
    response = await VectorDBItem.get_vector_db_items()
    return response

# get_vector_db_by_id
@app.get('/api/get_vector_db_item_by_id')
async def get_vector_db_by_id(id: str) -> VectorDBItemBase | None:
    response = await VectorDBItem.get_vector_db_by_id(id)
    return response

# get_vector_db_by_name
@app.get('/api/get_vector_db_item_by_name')
async def get_vector_db_by_name(name: str) -> VectorDBItemBase | None:
    response = await VectorDBItem.get_vector_db_by_name(name)
    return response

# update_vector_db
@app.post('/api/update_vector_db_items')
async def update_vector_db_items(items: Sequence[VectorDBItem]) -> Sequence[VectorDBItem]:
    response = await VectorDBItem.update_vector_db_items(items)
    return response

# delete_vector_db
@app.delete('/api/delete_vector_db_items')
async def delete_vector_db_items(items: Sequence[VectorDBItem]) -> None:
    response = await VectorDBItem.delete_vector_db_items(items)
    return response

# フォルダ内のベクトルDBインデックスを削除する
@app.delete('/api/delete_embeddings_by_folder')
async def delete_embeddings_by_folder(embedding_data_list: Sequence[EmbeddingData]) -> None:
    response = await LangChainUtilAPI.delete_embeddings_by_folder_api(embedding_data_list)
    return response

# delete_embeddings
@app.delete('/api/delete_embeddings')
async def delete_embeddings(embedding_data_list: Sequence[EmbeddingData]) -> None:
    response = await LangChainUtilAPI.delete_embeddings_api(embedding_data_list)
    return response

# update_embeddings
@app.post('/api/update_embeddings')
async def update_embeddings(embedding_data_list: Sequence[EmbeddingData]) -> None:
    response = await LangChainUtilAPI.update_embeddings_api(embedding_data_list)
    return response

# vector_search
@app.post('/api/vector_search')
async def vector_search(vector_search_request: VectorSearchRequest) -> Sequence[Document]:
    response = await LangChainUtilAPI.vector_search_api(vector_search_request)
    return response

########################
# ファイル関連
########################
# get_mime_type
@app.get('/api/get_mime_type')
async def get_mime_type(file_path: str) -> str:
    response = FileUtil.get_mime_type(file_path)
    return response

# get_sheet_names
@app.get('/api/get_sheet_names')
async def get_sheet_names(file_path: str) -> Sequence[str]:
    response = ExcelUtil.get_sheet_names(file_path)
    return response

# extract_excel_sheet
@app.post('/api/extract_excel_sheet')
async def extract_excel_sheet(file_path: str, sheet_name: str) -> str:
    response = ExcelUtil.extract_text_from_sheet(file_path, sheet_name)
    return response

# extract_text_from_file
@app.post('/api/extract_text_from_file')
async def extract_text_from_file(file_path: str) -> str:
    response: str = await FileUtil.extract_text_from_file_async(file_path)
    return response

# extract_base64_to_text
@app.get('/api/extract_base64_to_text')
async def extract_base64_to_text(extension: str, base64_data: str) -> str:
    response = await FileUtilAPI.extract_base64_to_text_async_api(extension, base64_data)
    return response

# extract_webpage
@app.get('/api/extract_webpage')
async def extract_webpage(url: str) -> WebPage:
    response = await WebUtilAPI.extract_webpage_api(url)
    return response

# export_to_excel
@app.get('/api/export_to_excel')
async def export_to_excel(file_path: str, columns: Sequence[str]) -> None:

    response = ExcelUtil.export_to_excel(file_path, columns)
    return response

# import_from_excel
@app.get('/api/import_from_excel')
async def import_from_excel(file_path: str) -> Sequence[dict]:
    response = ExcelUtil.import_from_excel(file_path)
    return response

# hello_world
@app.get('/api/hello_world')
async def hello_world() -> str:
    return "Hello, World!"

@app.post('/api/shutdown')
async def shutdown_server() -> None:
    pid = os.getpid()
    # Ctrl+CでSIGINTを送信してもらう
    os.kill(pid, 2)

async def main():
    """
    APIサーバのエントリーポイント。
    - APP_DATA_PATH等の環境変数を初期化
    - OpenAIPropsの環境変数チェック
    - アプリケーション初期化・ルーティング・サーバ起動
    """
    import asyncio
    # 第１引数はAPP_DATA_PATH
    if len(sys.argv) > 1:
        os.environ["APP_DATA_PATH"] = sys.argv[1]

    # APP_DATA_PATHを取得
    app_data_path = os.getenv("APP_DATA_PATH", None)
    if not app_data_path:
        raise ValueError("APP_DATA_PATH is required")

    # アプリケーション初期化
    """
    アプリケーション初期化時に呼び出される非同期関数。
    DBの初期化・マイグレーションを実施する。
    """
    await MainDBUtil.init(upgrade=True)

    port = os.getenv("API_SERVER_PORT", "5000")
    logger.info(f"port={port}")
    uvicorn_config = uvicorn.Config(app, host="0.0.0.0", port=int(port))
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == ('__main__'):
    import asyncio
    asyncio.run(main())