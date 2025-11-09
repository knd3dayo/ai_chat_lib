from typing import Any, cast
import json
from langchain_core.documents import Document
from vector_search_mcp.langchain.langchain_client import LangChainOpenAIClient
from vector_search_mcp.util.vector_db_client import VectorDBClient
from vector_search_mcp.model.models import EmbeddingData, VectorSearchRequest
from vector_search_mcp.langchain.langchain_vector_db import LangChainVectorDB
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem, VectorDBItemBase
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.api_modules.ai_app_data import AIAppData
from ai_chat_mcp.chat.chat_util import  ChatUtil, CompletionRequest, CompletionResponse

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class LangChainUtilAPI:
    
    @classmethod
    async def vector_search_api(cls, request_json: str) -> dict[str, Any]:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # queryを取得
        vector_search_request: VectorSearchRequest = await AIAppData.get_vector_search_request_objects(request_dict)
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

        return {"documents": [doc.model_dump() for doc in result]}

    @classmethod
    def update_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        vector_search_requests = AIAppData.get_embedding_request_objects(request_dict)

        # 現時点では処理なし
        return {}

    @classmethod
    async def delete_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        embedding_data = await AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()
        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))

        vector_db: LangChainVectorDB = vector_searcher.get_vector_db(embedding_data.vector_db_name)
        # delete_collectionを実行
        vector_db.delete_collection()

        return {}

    @classmethod
    async def delete_embeddings_by_folder_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data_dict = await AIAppData.get_embedding_request_objects(request_dict)
        embedding_data = EmbeddingData(**embedding_data_dict.model_dump())

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

        return {}

    @classmethod
    async def delete_embeddings_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = await AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()

        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))
        vector_db: LangChainVectorDB = vector_searcher.get_vector_db(embedding_data.vector_db_name)

        await vector_db.delete_document(embedding_data.source_id)

        return {}

    @classmethod
    async def update_embeddings_api(cls, request_json: str) -> dict:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # embedding_requestを取得
        embedding_data: EmbeddingData = await AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()
        vector_db_items = await VectorDBItem.get_vector_db_items()

        vector_searcher = VectorDBClient(langchain_openai_client=client, vector_dbs=cast(list[VectorDBItemBase], vector_db_items))
        vector_db: LangChainVectorDB = vector_searcher.get_vector_db(embedding_data.vector_db_name)

        # update_embeddingsを実行
        result = await vector_searcher.update_embeddings(embedding_data)
        return result

class ChatUtilAPI:
    chat_request_name = "chat_request"
    @classmethod
    async def run_openai_chat_async_api(cls, request_dict: dict) -> CompletionResponse:

        # context_jsonからChatRequestContextを生成
        chat_request_context = AIAppData.get_chat_request_context_objects(request_dict)
        # chat_requestを取得
        chat_request_dict = request_dict.get(cls.chat_request_name, None)
        if not chat_request_dict:
            raise ValueError("chat_request is not set")
        # chat_request_dictからChatRequestを生成
        chat_request_dict = CompletionRequest(**chat_request_dict)

        return await ChatUtil.run_openai_chat_async(chat_request_dict, chat_request_context)

    token_count_request_name = "token_count_request"
    @classmethod
    def get_token_count_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # input_textを取得
        token_count_request = request_dict.get(cls.token_count_request_name, None)
        if not token_count_request:
            raise ValueError("token_count_request is not set")
        model = token_count_request.get("model", None)
        if not model:
            raise ValueError("model is not set")
        input_text = token_count_request.get("input_text", "")
        if not input_text:
            raise ValueError("input_text is not set")
        result: dict = {}
        result["total_tokens"] = ChatUtil.get_token_count(model, input_text)
        return result

    chat_contatenate_request_name = "chat_contatenate_request"
