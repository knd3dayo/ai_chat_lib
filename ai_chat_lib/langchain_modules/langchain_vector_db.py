
import uuid
from typing import Tuple, List, Any, Union, Optional
from collections import defaultdict
import asyncio
from pydantic import BaseModel, Field, ConfigDict

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.runnables import chain
from langchain_core.callbacks import (
    CallbackManagerForRetrieverRun,
)
from openai import RateLimitError

from ai_chat_lib.langchain_modules.langchain_client import LangChainOpenAIClient
from ai_chat_lib.langchain_modules.langchain_doc_store import SQLDocStore

from ai_chat_lib.db_modules.embedding_data import EmbeddingData
from ai_chat_lib.db_modules.content_folder import ContentFolder

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class CustomMultiVectorRetriever(MultiVectorRetriever):
    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        """Get documents relevant to a query.
        Args:
            query: String to find relevant documents for
            run_manager: The callbacks handler to use
        Returns:
            List of relevant documents
        """
        results = self.vectorstore.similarity_search_with_relevance_scores(query, **self.search_kwargs)

        # Map doc_ids to list of sub-documents, adding scores to metadata
        id_to_doc = defaultdict(list)
        for doc, score in results:
            doc_id = doc.metadata.get("doc_id")
            if doc_id:
                doc.metadata["score"] = score
                id_to_doc[doc_id].append(doc)

        # Fetch documents corresponding to doc_ids, retaining sub_docs in metadata
        docs = []
        for _id, sub_docs in id_to_doc.items():
            docstore_docs = self.docstore.mget([_id])
            if docstore_docs:
                docstore_doc: Optional[Document]= docstore_docs[0]
                if docstore_doc is not None:
                    docstore_doc.metadata["sub_docs"] = sub_docs
                    docs.append(docstore_doc)

        return docs

class LangChainVectorDB(BaseModel):
    """
    LangChainのベクトルDBを利用するための基底クラス。
    """
    langchain_openai_client: LangChainOpenAIClient = Field(..., description="LangChain OpenAI Client")
    vector_db_url: str = Field(..., description="Vector DBのURL")
    collection_name: str = Field(default="", description="コレクション名")
    multi_vector_doc_store_url: str = Field(default="", description="MultiVectorRetrieverを利用する場合のDocStoreのURL")
    chunk_size: int = Field(default=4000, description="テキストを分割するチャンクサイズ")
    use_multi_vector_retriever: bool = Field(default=False, description="MultiVectorRetrieverを利用するかどうか")
    multi_vector_chunk_size: int = Field(default=1000, description="MultiVectorRetrieverを利用する場合のチャンクサイズ")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    db : Union[VectorStore, None] = Field(default=None, description="VectorStoreのインスタンス")
    doc_store: Union[SQLDocStore, None] = Field(default=None, description="SQLDocStoreのインスタンス")


    # document_idのリストとmetadataのリストを返す
    def _get_document_ids_by_tag(self, name: str = "", value: str = "") -> Tuple[List[str], List[dict[str, Any]]]:
        # 未実装例外をスロー
        raise NotImplementedError("Not implemented")

    async def _delete(self, doc_ids:list=[]):
        if len(doc_ids) == 0:
            return
        if self.db is None:
            raise ValueError("db is None")

        await self.db.adelete(ids=doc_ids)

        return len(doc_ids)    

    def _delete_collection(self):
        # self.dbがdelete_collectionメソッドを持っている場合はそれを呼び出す
        if hasattr(self.db, "delete_collection"):
            self.db.delete_collection() # type: ignore

    async def __add_document(self, document: Document):
        if self.db is None:
            raise ValueError("db is None")
        await self.add_doucment_with_retry(self.db, [document])    
    
    async def __add_multivector_document(self, source_document: Document):

        # doc_idを取得
        doc_id = source_document.metadata.get("doc_id", None)
        # doc_idがNoneの場合はエラー
        if doc_id is None:
            raise ValueError("doc_id is None")

        sub_docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.multi_vector_chunk_size)
        splited_docs = text_splitter.split_documents([source_document])
        if len(splited_docs) == 0:
            raise ValueError("splited_docs is empty")
        for sub_doc in splited_docs:
            sub_doc.metadata["doc_id"] = doc_id
            sub_docs.append(sub_doc)

        # Retoriverを作成
        retriever = self.create_retriever()
        # ドキュメントを追加
        await self.add_doucment_with_retry(retriever.vectorstore, sub_docs)    

        # 元のドキュメントをDocStoreに保存
        param = []
        param.append((doc_id, source_document))
        retriever.docstore.mset(param)

    def __create_decorated_retriever(self, vectorstore: VectorStore, **kwargs: Any):
        # ベクトル検索の結果にスコアを追加する
        @chain
        def retriever(query: str) -> list[Document]:
            result = []
            params = kwargs.copy()
            params["query"] = query
            search_results = vectorstore.similarity_search_with_relevance_scores(**params)
            if not search_results:
                return []

            docs, scores = zip(*search_results)
            for doc, score in zip(docs, scores):
                doc.metadata["score"] = score
                result.append(doc)
            return result   

        return retriever

    async def add_document_list(self, data: EmbeddingData, chunk_size: int) -> list[Document]:
        
        document_list = []

        # テキストをサニタイズ
        content_text = self._sanitize_text(data.content)
        # テキストをchunk_sizeで分割
        text_list = self._split_text(content_text, chunk_size=chunk_size)
        for text in text_list:
            doc_id = str(uuid.uuid4())
            logger.info(f"folder_path:{data.folder_path}")
            # folderを取得
            folder = await ContentFolder.get_content_folder_by_path(data.folder_path)
            if not folder:
                # folderが見つからない場合はfolder_idを空にする
                logger.warning(f"Folder not found for path: {data.folder_path}. Setting folder_id to empty.")
                folder_id = ""
            else:
                logger.info(f"Folder found: {folder.id} for path: {data.folder_path}")
                # folder_idを取得
                folder_id = folder.id
                if not folder_id:
                    raise ValueError(f"Folder ID not found for path: {data.folder_path}")
            
            metadata = LangChainVectorDB.create_metadata(
                doc_id, data.source_id, folder_id, "", data.source_path, data.description)
            logger.debug("metadata:", metadata)
            document = Document(page_content=text, metadata=metadata)
            document_list.append(document)

        # MultiVectorRetrieverの場合はadd_multivector_documentを呼び出す
        if self.multi_vector_doc_store_url:
            for document in document_list:
                await self.__add_multivector_document(document)
            return document_list
        else:
            for document in document_list:
                await self.__add_document(document)
            return document_list


    # テキストをサニタイズする
    def _sanitize_text(self, text: str) -> str:
        # textが空の場合は空の文字列を返す
        if not text or len(text) == 0:
            return ""
        import re
        # 1. 複数の改行を1つの改行に変換
        text = re.sub(r'\n+', '\n', text)
        # 2. 複数のスペースを1つのスペースに変換
        text = re.sub(r' +', ' ', text)

        return text

    def _split_text(self, text: str, chunk_size: int):
        text_list : list[str] = []
        # textが空の場合は空のリストを返す
        if not text or len(text) == 0:
            return text_list
        
        # テキストをchunk_sizeで分割
        for i in range(0, len(text), chunk_size):
            text_list.append(text[i:i + chunk_size])
        return text_list

    ########################################
    # パブリック
    ########################################
    def create_retriever(self, search_kwargs: dict[str, Any] = {}) -> Any:
        # ベクトルDB検索用のRetrieverオブジェクトの作成と設定

        if not search_kwargs:
            # デフォルトの検索パラメータを設定
            logger.info("search_kwargs is empty. Set default search_kwargs")
            search_kwargs = {"k": 10}

        # IsUseMultiVectorRetriever=Trueの場合はMultiVectorRetrieverを生成
        if self.db is None:
            raise ValueError("db is None")
        if self.multi_vector_doc_store_url:
            logger.info("Creating MultiVectorRetriever")
            if self.doc_store is None:
                raise ValueError("doc_store is None")
            
            retriever = CustomMultiVectorRetriever(
                vectorstore=self.db,
                docstore=self.doc_store,
                id_key="doc_id",
                search_kwargs=search_kwargs
            )

        else:
            logger.debug("Creating a regular Retriever")
            retriever = self.__create_decorated_retriever(self.db, **search_kwargs)
         
        return retriever


    def delete_collection(self):
        # ベクトルDB固有の削除メソッドを呼び出してコレクションを削除
        self._delete_collection()

    async def delete_folder(self, folder_id: str):
        # ベクトルDB固有のvector id取得メソッドを呼び出し。
        vector_ids, _ = self._get_document_ids_by_tag("older_id", folder_id)

        # vector_idsが空の場合は何もしない
        if len(vector_ids) == 0:
            return 0

        # DocStoreから削除
        if self.multi_vector_doc_store_url and self.doc_store is not None:
            await self.doc_store.amdelete(vector_ids)

        # ベクトルDB固有の削除メソッドを呼び出し
        await self._delete(vector_ids)

    async def delete_document(self, source_id: str):
        # ベクトルDB固有のvector id取得メソッドを呼び出し。
        doc_ids, _ = self._get_document_ids_by_tag("source_id", source_id)

        # vector_idsが空の場合は何もしない
        if len(doc_ids) == 0:
            return 0

        # DocStoreから削除
        if self.multi_vector_doc_store_url and self.doc_store is not None:
            await self.doc_store.amdelete(doc_ids)

        # ベクトルDB固有の削除メソッドを呼び出し
        await self._delete(doc_ids)

    async def update_embeddings(self, params: EmbeddingData):
        
        # 既に存在するドキュメントを削除
        await self.delete_document(params.source_id)
        # ドキュメントを格納する。
        await self.add_document_list(params, chunk_size=self.chunk_size)

    # RateLimitErrorが発生した場合は、指数バックオフを行う
    async def add_doucment_with_retry(self, vector_db: VectorStore, documents: list[Document], max_retries: int = 5, delay: float = 1.0):
        for attempt in range(max_retries):
            try:
                await vector_db.aadd_documents(documents=documents)
                return
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"RateLimitError: {e}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Max retries reached. Failed to add documents: {e}")
                    break
            except Exception as e:
                logger.error(f"Error adding documents: {e}")
                break

    @classmethod
    def create_metadata(cls, 
                        doc_id: str, source_id: str, folder_id: str, 
                        folder_path: str, source_path: str,
                        description: str, score = 0.0
                        ) -> dict[str, Any]:
        metadata = {
            "folder_id": folder_id, "folder_path": folder_path, "source_path": source_path,   
            "description": description, 
            "doc_id": doc_id, "source_id": source_id, "source_type": 0, "score": score
        }
        return metadata

    @classmethod
    def create_metadata_from_document(cls, document: Document):
        metadata = document.metadata
        source_id = metadata.get("source_id", "")
        folder_id = metadata.get("folder_id", "")
        doc_id = metadata.get("doc_id", "")
        source_path = metadata.get("source_path", "")
        description = metadata.get("description", "")
        score = metadata.get("score", 0)
        folder_path = metadata.get("folder_path", "")
        return cls.create_metadata(doc_id, source_id, folder_id, folder_path ,source_path, description, score)

    
