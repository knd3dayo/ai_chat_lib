from typing import Any
import json
from ai_chat_lib.chat_modules.langchain.langchain_util import LangChainUtil
from ai_chat_lib.chat_modules.langchain.embedding_data import EmbeddingData
from ai_chat_lib.chat_modules.langchain.langchain_vector_db import LangChainVectorDB
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from ai_chat_lib.chat_modules.langchain.vector_search_request import VectorSearchRequest
from ai_chat_lib.chat_modules.llm.openai_util import OpenAIProps
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.api_modules.ai_app_data import AIAppData
from ai_chat_lib.chat_modules.util.chat_util import  ChatUtil, CompletionRequest, CompletionOutput


class LangChainUtilAPI:
    
    @classmethod
    async def vector_search_api(cls, request_json: str) -> dict[str, Any]:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # queryを取得
        vector_search_requests: list[VectorSearchRequest] = await AIAppData.get_vector_search_requests_objects(request_dict)
        openai_props = OpenAIProps()
        result = await LangChainUtil.vector_search(openai_props, vector_search_requests)
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
        openai_props = OpenAIProps()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        # delete_collectionを実行
        vector_db.delete_collection()

        return {}

    @classmethod
    async def delete_embeddings_by_folder_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = AIAppData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            # VectorDBItemが見つからない場合は空の辞書を返す
            return {}
        
        # LangChainVectorDBを生成
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)

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
        openai_props = OpenAIProps()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        await vector_db.delete_document(embedding_data.source_id)

        return {}

    @classmethod
    async def update_embeddings_api(cls, request_json: str) -> dict:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # embedding_requestを取得
        embedding_data: EmbeddingData = AIAppData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps()
        # update_embeddingsを実行
        result = await LangChainUtil.update_embeddings(openai_props, embedding_data)
        return result

class ChatUtilAPI:
    chat_request_name = "chat_request"
    @classmethod
    async def run_openai_chat_async_api(cls, request_dict: dict) -> CompletionOutput:

        openai_props = OpenAIProps()
        # context_jsonからVectorSearchRequestを生成
        vector_search_requests = await AIAppData.get_vector_search_requests_objects(request_dict)
        # context_jsonからChatRequestContextを生成
        chat_request_context = AIAppData.get_chat_request_context_objects(request_dict)
        # chat_requestを取得
        chat_request_dict = request_dict.get(cls.chat_request_name, None)
        if not chat_request_dict:
            raise ValueError("chat_request is not set")
        # chat_request_dictからChatRequestを生成
        chat_request_dict = CompletionRequest(**chat_request_dict)

        return await ChatUtil.run_openai_chat_async(openai_props, chat_request_context, chat_request_dict, vector_search_requests)

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
