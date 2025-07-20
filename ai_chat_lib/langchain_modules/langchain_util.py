
import json, sys
from typing import Any, Generator
from langchain.docstore.document import Document


from ai_chat_lib.langchain_modules.langchain_client import LangChainOpenAIClient, LangChainChatParameter
from ai_chat_lib.langchain_modules.langchain_vector_db import LangChainVectorDB

from ai_chat_lib.llm_modules.openai_util import OpenAIProps
from ai_chat_lib.langchain_modules.vector_search_request import VectorSearchRequest
from ai_chat_lib.langchain_modules.embedding_data import EmbeddingData
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from ai_chat_lib.db_modules.content_folder import ContentFolder

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)


class LangChainUtil:

    @classmethod
    async def vector_search_api(cls, request_json: str) -> dict[str, Any]:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # queryを取得
        vector_search_requests: list[VectorSearchRequest] = await VectorSearchRequest.get_vector_search_requests_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()
        result = await cls.vector_search(openai_props, vector_search_requests)
        return {"documents": [doc.model_dump() for doc in result]}

    @classmethod
    def update_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        vector_search_requests = EmbeddingData.get_embedding_request_objects(request_dict)

        # 現時点では処理なし
        return {}

    @classmethod
    async def delete_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

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
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        
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
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

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
        embedding_data: EmbeddingData = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()
        # update_embeddingsを実行
        result = await cls.update_embeddings(openai_props, embedding_data)
        return result

    @classmethod
    async def update_embeddings(cls, openai_props: OpenAIProps, embedding_data: EmbeddingData) -> dict:
        """
        ベクトルDBのコンテンツインデックスを更新する
        :param openai_props: OpenAIProps
        :param embedding_data: EmbeddingData
        :return: dict
        """
        vector_db_item = await VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        
        # LangChainVectorDBを生成
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        await vector_db.update_embeddings(embedding_data)

        return {}   

    chat_request_name = "chat_request"

    @classmethod
    def get_vector_db(cls, openai_props: OpenAIProps, vector_db_props: VectorDBItem, embedding_model: str) -> LangChainVectorDB:

        langchain_openai_client = LangChainOpenAIClient(props=openai_props, embedding_model=embedding_model)

        vector_db_url = vector_db_props.vector_db_url
        if vector_db_props.is_use_multi_vector_retriever:
            doc_store_url = vector_db_props.doc_store_url
        else:
            doc_store_url = ""
        collection_name = vector_db_props.collection_name
        chunk_size = vector_db_props.chunk_size

        # ベクトルDBのタイプがChromaの場合
        if vector_db_props.vector_db_type == 1:
            from ai_chat_lib.langchain_modules.langchain_vector_db_chroma import LangChainVectorDBChroma
            return LangChainVectorDBChroma(
                langchain_openai_client = langchain_openai_client,
                vector_db_url = vector_db_url,
                collection_name = collection_name,
                doc_store_url= doc_store_url, 
                chunk_size = chunk_size)
        # ベクトルDBのタイプがPostgresの場合
        elif vector_db_props.vector_db_type == 2:
            from ai_chat_lib.langchain_modules.langchain_vector_db_pgvector import LangChainVectorDBPGVector
            return LangChainVectorDBPGVector(
                langchain_openai_client = langchain_openai_client,
                vector_db_url = vector_db_url,
                collection_name = collection_name,
                doc_store_url= doc_store_url, 
                chunk_size = chunk_size)
                
        else:
            # それ以外の場合は例外
            raise ValueError("VectorDBType is invalid")

    # ベクトル検索を行う
    @classmethod
    async def vector_search(cls, openai_props: OpenAIProps, vector_search_requests: list[VectorSearchRequest]) -> list[Document]:    

        if not openai_props:
            raise ValueError("openai_props is None")

        result_documents = []

        # vector_db_propsの要素毎にRetrieverを作成して、検索を行う
        for request in vector_search_requests:
            # debug request.nameが設定されているか確認
            if not request.name:
                raise ValueError("request.name is not set")
            if not request.query:
                raise ValueError("request.query is not set")

            # vector_db_itemを取得
            vector_db_item = await VectorDBItem.get_vector_db_by_name(request.name)
            if vector_db_item is None:
                logger.error(f"VectorDBItem with name {request.name} not found.")
                raise ValueError(f"vector_db_item is None. name:{request.name}")
            
            langchain_db = cls.get_vector_db(openai_props, vector_db_item, request.model)
            
            # デバッグ出力
            logger.info('ベクトルDBの設定')
            logger.info(f'''
                        name:{vector_db_item.name} vector_db_description:{vector_db_item.description} 
                        VectorDBTypeString:{vector_db_item.get_vector_db_type_string()} VectorDBURL:{vector_db_item.vector_db_url} 
                        CollectionName:{vector_db_item.collection_name}'
                        ChunkSize:{vector_db_item.chunk_size} IsUseMultiVectorRetriever:{vector_db_item.is_use_multi_vector_retriever}
                        ''')

            logger.info(f'Query: {request.query}')
            logger.info(f'SearchKwargs:{request.search_kwargs}')
            documents =  await langchain_db.vector_search(request.query, request.search_kwargs)
            result_documents.extend(documents)

        return result_documents
    
