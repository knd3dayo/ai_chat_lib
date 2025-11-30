from typing import Any, cast, Sequence
import json
from langchain_core.documents import Document
from vector_search_mcp.langchain.langchain_client import LangChainOpenAIClient
from vector_search_mcp.util.vector_db_client import VectorDBClient
from vector_search_mcp.model.models import EmbeddingData, VectorSearchRequest
from vector_search_mcp.langchain.langchain_vector_db import LangChainVectorDB
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem, VectorDBItemBase
from ai_chat_lib.db_modules.content_folder import ContentFolder
from vector_search_mcp.model.models import EmbeddingData, VectorSearchRequest

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class LangChainUtilAPI:
    
    @classmethod
    async def vector_search_api(cls, vector_search_request: VectorSearchRequest) -> Sequence[Document]:

        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()
        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))

        result: list[Document] = await vector_searcher.vector_search(vector_search_request)
        # folder_idからfolder_pathを設定
        for doc in result:
            folder_id = doc.metadata.get("folder_id", None)
            if folder_id:
                folder_path = await ContentFolder.get_content_folder_path_by_id(folder_id)
                doc.metadata["folder_path"] = folder_path

        return result

    @classmethod
    async def delete_embedding_by_folder_api(cls, embedding_data: EmbeddingData) -> None:

        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()

        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))
        vector_db: LangChainVectorDB = vector_searcher.get_vector_db(embedding_data.vector_db_name)

        # folder_idを取得
        folder_id = embedding_data.metadata.get("folder_id", None)
        if folder_id is None:
            raise ValueError(f"folder_id not found.")
        # delete_folder_embeddingsを実行
        await vector_db.delete_documents_by_tag("folder_id", folder_id)

    @classmethod
    async def delete_embeddings_by_folder_api(cls, embedding_data_list: Sequence[EmbeddingData]) -> None:
        for embedding_data in embedding_data_list:
            await cls.delete_embedding_by_folder_api(embedding_data)

    @classmethod
    async def delete_embedding_api(cls, embedding_data: EmbeddingData) -> None:

        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()

        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))
        vector_db: LangChainVectorDB = vector_searcher.get_vector_db(embedding_data.vector_db_name)

        await vector_db.delete_document(embedding_data.source_id)

    @classmethod
    async def delete_embeddings_api(cls, embedding_data_list: Sequence[EmbeddingData]) -> None:
        for embedding_data in embedding_data_list:
            await cls.delete_embedding_api(embedding_data)  

    @classmethod
    async def update_embedding_api(cls, embedding_data: EmbeddingData) -> None:
        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()

        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))

        # update_embeddingsを実行
        await vector_searcher.update_embeddings(embedding_data)
    
    @classmethod
    async def update_embeddings_api(cls, embedding_data_list: Sequence[EmbeddingData]) -> None:
        for embedding_data in embedding_data_list:
            await cls.update_embedding_api(embedding_data)


from typing import Sequence
from web_search_mcp.web_modules.web_util import WebUtil

from pydantic import BaseModel

class WebPage(BaseModel):
    url: str
    content: str
    urls: Sequence[tuple[str, str]]  # (url, title)のタプルのリスト

class WebUtilAPI:

    @classmethod
    async def extract_webpage_api(cls, url: str) -> WebPage:
        if url is None:
            raise ValueError("URL is not set in the web_request object.")
        text, urls = await WebUtil.extract_webpage(url)
        webpage = WebPage(
            url=url,
            content=text,
            urls=urls
        )
        return webpage

import json
import os
import base64
from extract_file_mcp.file_modules.file_util import FileUtil, ExcelUtil

class FileUtilAPI:

    @classmethod
    async def extract_base64_to_text_async_api(cls, extension: str, base64_data: str) -> str:

        # サイズが0の場合は空文字を返す
        if not base64_data or len(base64_data) == 0:
            return ""

        # base64からバイナリデータに変換
        base64_data_bytes = base64.b64decode(base64_data)

        # 拡張子の指定。extensionがNoneまたは空の場合は設定しない.空でない場合は"."を先頭に付与
        suffix = ""
        if extension is not None and extension != "":
            suffix = "." + extension
        # base64データから一時ファイルを生成
        import aiofiles.tempfile
        async with aiofiles.tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=suffix) as temp:
            await temp.write(base64_data_bytes)
            await temp.close()
            # 一時ファイルからテキストを抽出
            temp_path = temp.name if isinstance(temp.name, str) else str(temp.name)
            text = await FileUtil.extract_text_from_file_async(temp_path)
            # 一時ファイルを削除
            os.remove(temp_path)
            return text

        return text


