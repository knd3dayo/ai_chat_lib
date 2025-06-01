
import json, sys
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from langchain.docstore.document import Document
from langchain_community.callbacks.manager import get_openai_callback
import langchain
from langchain_core.tools.structured import StructuredTool

from typing import Any
from pydantic import BaseModel, Field


from ai_chat_lib.langchain_modules.langchain_client import LangChainOpenAIClient, LangChainChatParameter
from ai_chat_lib.langchain_modules.langchain_vector_db import LangChainVectorDB

from ai_chat_lib.llm_modules.openai_util import OpenAIProps
from ai_chat_lib.db_modules import *

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)



class CustomToolInput(BaseModel):
    question: str = Field(description="question")

class RetrievalQAUtil:

    def __init__(self, client: LangChainOpenAIClient, vector_search_requests:list[VectorSearchRequest]):
        self.client = client
        self.vector_search_requests = vector_search_requests

        # ツールのリストを作成
        self.tools = self.create_vector_search_tools(self.client, self.vector_search_requests)

    
    # intermediate_stepsをシリアライズする
    def __serialize_intermediate_step(self, step):
        return {
            "tool": step[0].tool,
            "tool_input": step[0].tool_input,
            "log": step[0].log,
            "output": str(step[1]),
        }


    # ベクトル検索結果を返すToolを作成する関数
    def create_vector_search_tools(self, client: LangChainOpenAIClient, vector_search_requests: list[VectorSearchRequest]) -> list[Any]:
        tools = []
        for i in range(len(vector_search_requests)):
            item = vector_search_requests[i]
            vector_db_item: VectorDBItem = item.get_vector_db_item()
            # ベクトルDBのURLを取得
            # description item.VectorDBDescriptionが空の場合はデフォルトの説明を設定
            description = vector_db_item.description
            vector_db_url = vector_db_item.vector_db_url
            doc_store_url = ""
            if vector_db_item.is_use_multi_vector_retriever:
                doc_store_url = vector_db_item.doc_store_url
            collection_name = vector_db_item.collection_name
            chunk_size = vector_db_item.chunk_size

            # ツールを作成
            def vector_search_function(question: str) -> list[Document]:
                # Retrieverを作成
                search_kwargs = {"k": 4}

                retriever = LangChainVectorDB(client, vector_db_url, collection_name, doc_store_url, chunk_size).create_retriever(search_kwargs)
                docs: list[Document] = retriever.invoke(question)
                # page_contentを取得
                result_docs = []
                for doc in docs:
                    result_docs.append(doc)
                return result_docs

            # StructuredTool.from_functionを使ってToolオブジェクトを作成
            vector_search_tool = StructuredTool.from_function(
                func=vector_search_function, name="vector_search_tool-" + str(i), description=description, args_schema=CustomToolInput  
            )

            tools.append(vector_search_tool)

        return tools


class LangChainUtil:

    @classmethod
    def vector_search_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # queryを取得
        vector_search_requests: list[VectorSearchRequest] = VectorSearchRequest.get_vector_search_requests_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()
        result = cls.vector_search(openai_props, vector_search_requests)
        return result

    @classmethod
    def update_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        vector_search_requests = EmbeddingData.get_embedding_request_objects(request_dict)

        # 現時点では処理なし
        return {}

    @classmethod
    def delete_collection_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # ChatRequestContextからVectorDBItemを生成
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

        vector_db_item = VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        # delete_collectionを実行
        vector_db.delete_collection()

        return {}

    @classmethod
    def delete_embeddings_by_folder_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

        vector_db_item = VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        
        # LangChainVectorDBを生成
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)

        folder_id = embedding_data.folder_id
        # delete_folder_embeddingsを実行
        vector_db.delete_folder(folder_id)

        return {}

    @classmethod
    def delete_embeddings_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # embedding_requestを取得
        embedding_data = EmbeddingData.get_embedding_request_objects(request_dict)
        openai_props = OpenAIProps.create_from_env()

        vector_db_item = VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        vector_db.delete_document(embedding_data.source_id)

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
        vector_db_item = VectorDBItem.get_vector_db_by_name(embedding_data.name)
        if vector_db_item is None:
            raise ValueError(f"VectorDBItem with name {embedding_data.name} not found.")
        
        # LangChainVectorDBを生成
        vector_db: LangChainVectorDB = LangChainUtil.get_vector_db(openai_props, vector_db_item, embedding_data.model)
        await vector_db.update_document(embedding_data)

        return {}   

    chat_request_name = "chat_request"

    @classmethod
    def get_vector_db(cls, openai_props: OpenAIProps, vector_db_props: VectorDBItem, embedding_model: str) -> LangChainVectorDB:

        langchain_openai_client = LangChainOpenAIClient(openai_props, embedding_model)

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
            return LangChainVectorDBChroma(langchain_openai_client, vector_db_url, collection_name, doc_store_url, chunk_size)
        # ベクトルDBのタイプがPostgresの場合
        elif vector_db_props.vector_db_type == 2:
            from ai_chat_lib.langchain_modules.langchain_vector_db_pgvector import LangChainVectorDBPGVector
            return LangChainVectorDBPGVector(langchain_openai_client, vector_db_url, collection_name, doc_store_url, chunk_size)
        else:
            # それ以外の場合は例外
            raise ValueError("VectorDBType is invalid")

    # ベクトル検索を行う
    @classmethod
    def vector_search(cls, openai_props: OpenAIProps, vector_search_requests: list[VectorSearchRequest]) -> dict[str, Any]:    

        if not openai_props:
            raise ValueError("openai_props is None")
        
            
        result = []
        # vector_db_propsの要素毎にRetrieverを作成して、検索を行う
        for request in vector_search_requests:
            # debug request.nameが設定されているか確認
            if not request.name:
                raise ValueError("request.name is not set")
            if not request.query:
                raise ValueError("request.query is not set")

            # vector_db_itemを取得
            vector_db_item = VectorDBItem.get_vector_db_by_name(request.name)
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
            retriever = langchain_db.create_retriever(request.search_kwargs)
            documents: list[Document] = retriever.invoke(request.query)

            # 重複排除用のリストを作成
            doc_ids = []

            for doc in documents:
                # doc_idを取得
                doc_id = doc.metadata.get("doc_id", "")
                # 既にdoc_idが存在する場合はスキップ
                if doc_id in doc_ids:
                    continue
                # doc_idを追加
                doc_ids.append(doc_id)
                # folder_idを取得
                folder_id = doc.metadata.get("folder_id", "")
                if folder_id:
                    # folder_idからfolder_pathを取得
                    folder_path = ContentFoldersCatalog.get_content_folder_path_by_id(folder_id)
                    if folder_path:
                        doc.metadata["folder_path"] = folder_path
                    else:
                        # folder_pathが存在しない場合は空文字を設定
                        doc.metadata["folder_path"] = ""

                content = doc.page_content
                doc_dict = LangChainVectorDB.create_metadata_from_document(doc)
                doc_dict["content"] = content

                sub_docs: list[Document]= doc.metadata.get("sub_docs", [])
                # sub_docsの要素からcontent, source, source_url,scoreを取得してdictのリストに追加
                sub_docs_result = []
                for sub_doc in sub_docs:
                    content = sub_doc.page_content
                    # folder_idを取得
                    folder_id = sub_doc.metadata.get("folder_id", "")
                    if folder_id:
                        # folder_idからfolder_pathを取得
                        folder_path = ContentFoldersCatalog.get_content_folder_path_by_id(folder_id)
                        if folder_path:
                            sub_doc.metadata["folder_path"] = folder_path
                        else:
                            # folder_pathが存在しない場合は空文字を設定
                            sub_doc.metadata["folder_path"] = ""

                    sub_doc_dict = LangChainVectorDB.create_metadata_from_document(sub_doc)
                    sub_doc_dict["content"] = content
                    sub_docs_result.append(sub_doc_dict)

                doc_dict["sub_docs"] = sub_docs_result
                result.append(doc_dict)

            # logger.debug(f"documents:\n{documents}")
            
        return {"documents": result}
    
