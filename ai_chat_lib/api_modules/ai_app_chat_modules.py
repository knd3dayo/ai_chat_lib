from typing import Any
import json
from vector_search_mcp.langchain.langchain_util import LangChainUtil, LangChainOpenAIClient
from vector_search_mcp.langchain.embedding_data import EmbeddingData
from vector_search_mcp.langchain.langchain_vector_db import LangChainVectorDB
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from vector_search_mcp.langchain.langchain_util import VectorSearchRequest
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.api_modules.ai_app_data import AIAppData
from ai_chat_mcp.chat.chat_util import  ChatUtil, CompletionRequest, CompletionResponse


class LangChainUtilAPI:
    
    @classmethod
    async def vector_search_api(cls, request_json: str) -> dict[str, Any]:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # queryを取得
        vector_search_request: VectorSearchRequest = await AIAppData.get_vector_search_request_objects(request_dict)
        client = LangChainOpenAIClient()
        vector_db_item = await VectorDBItem.get_vector_db_by_name(vector_search_request.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {vector_search_request.name} not found.")

        result = await LangChainUtil.vector_search(client, vector_db_item, vector_search_request)
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
        embedding_data = AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(client, vector_db_item)
        # delete_collectionを実行
        vector_db.delete_collection()

        return {}

    @classmethod
    async def delete_embeddings_by_folder_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            # VectorDBItemが見つからない場合は空の辞書を返す
            return {}
        
        # LangChainVectorDBを生成
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(client, vector_db_item)

        folder = await ContentFolder.get_content_folder_by_path(embedding_data.folder_path)
        folder_id = folder.id if folder else None
        if folder_id is None:
            raise ValueError(f"Folder with path {embedding_data.folder_path} not found.")
        # delete_folder_embeddingsを実行
        await vector_db.delete_folder(folder_id)

        return {}

    @classmethod
    async def delete_embeddings_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(client, vector_db_item)
        await vector_db.delete_document(embedding_data.source_id)

        return {}

    @classmethod
    async def update_embeddings_api(cls, request_json: str) -> dict:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # embedding_requestを取得
        embedding_data: EmbeddingData = AIAppData.get_embedding_request_objects(request_dict)
        client = LangChainOpenAIClient()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")

        # update_embeddingsを実行
        result = await LangChainUtil.update_embeddings(client, vector_db_item, embedding_data)
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
