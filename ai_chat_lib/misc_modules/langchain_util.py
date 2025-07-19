import os
import json
import asyncio
import uuid
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List, Dict, Any, Union, Tuple
from collections import defaultdict

from openai import RateLimitError
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_core.vectorstores import VectorStore # type: ignore

import chromadb
import chromadb.config
from langchain_chroma.vectorstores import Chroma # type: ignore
from langchain.docstore.document import Document

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain_core.runnables import chain
from langchain_core.callbacks import (
    CallbackManagerForRetrieverRun,
)
from ai_chat_lib.langchain_modules.langchain_doc_store import SQLDocStore
from langchain_core.retrievers import BaseRetriever
import logging 
logger = logging.getLogger(__name__)

class EmbeddingData(BaseModel):
    # content: str embedding対象のテキスト
    content: str = Field(..., description="Embedding対象のテキスト")
    # description: str embeddingの説明
    description: Optional[str] = Field(default="", description="Embeddingの説明")
    # source_path: str embeddingのソースパス. オプション
    source_path: Optional[str] = Field(default=None, description="Embeddingのソースパス. オプション")
    # folder_path: str embeddingのフォルダ名. オプション
    folder_path: Optional[str] = Field(default=None, description="Embeddingのフォルダ名. オプション")

class VectorRetrieverWrapper:
    """
    A wrapper class for vector retrievers.
    This class is used to create a retriever with a specific vector store and search parameters.
    """

    def __init__(self, 
                 vectorstore: VectorStore, doc_id: str, 
                 search_kwargs: dict[str, Any] = {}, use_multi_vector_retriever: bool = False, docstore: Optional[SQLDocStore] = None
                 ):
        self.vectorstore = vectorstore
        self.doc_id = doc_id
        self.search_kwargs = search_kwargs
        self.use_multi_vector_retriever = use_multi_vector_retriever
        self.docstore = docstore
        self.retriever = self.__create_retriever()
        
    def __create_retriever(self) -> BaseRetriever:
        """
        Create a retriever with the specified vector store and search parameters.
        Returns:
            BaseRetriever: A retriever object for vector search.
        """
        if self.use_multi_vector_retriever:
            if not self.docstore:
                raise ValueError("docstore must be provided for MultiVectorRetriever.")

            logger.debug("Creating a MultiVectorRetriever")
            return MultiVectorRetriever(
                vectorstore=self.vectorstore,
                docstore=self.docstore,
                id_key=self.doc_id,
                search_kwargs=self.search_kwargs
            )
        else:
            logger.debug("Creating a regular Retriever")
            return CustomBaseRetriever(self.vectorstore, **self.search_kwargs)


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

class CustomBaseRetriever(BaseRetriever):
    """
    Custom retriever that wraps a vector store and allows for custom search parameters.
    This class is used to create a retriever with a specific vector store and search parameters.
    """

    def __init__(self, vectorstore: VectorStore, **kwargs: Any):
        self.vectorstore = vectorstore
        self.kwargs = kwargs

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        result = []
        params = self.kwargs.copy()
        params["query"] = query
        search_results = self.vectorstore.similarity_search_with_relevance_scores(**params)
        if not search_results:
            return []

        docs, scores = zip(*search_results)
        for doc, score in zip(docs, scores):
            doc.metadata["score"] = score
            result.append(doc)
        return result   


class LangChainOpenAIClient(BaseModel):
    """
    LangChain OpenAI Client for generating embeddings.
    This class supports both OpenAI and Azure OpenAI.
    Attributes:
        api_key (str): API key for OpenAI or Azure OpenAI.
        model (str): Model name for embeddings.
        azure_openai (bool): Flag to indicate if Azure OpenAI is used.
        endpoint (Optional[str]): Endpoint for Azure OpenAI, required if azure_openai is True.
        version (Optional[str]): API version for Azure OpenAI, required if azure_openai is True.
    """
    api_key: str = Field(..., description="API key for OpenAI or Azure OpenAI")
    model: str = Field(..., description="Model name for embeddings")
    # flag for OpenAI or Azure OpenAI. Defaults to OpenAI if not specified.
    azure_openai: bool = Field(default=False, description="Use Azure OpenAI if True, otherwise use OpenAI")
    # optional parameters for Azure OpenAI
    endpoint: Optional[str] = Field(default="", description="Endpoint for Azure OpenAI")
    version: Optional[str] = Field(default="", description="API version for Azure OpenAI")


    def get_embedding_client(self):
        params: Dict[str, Any] = {
            "api_key": self.api_key,
            "model": self.model,
        }
        # Check if using Azure OpenAI or OpenAI
        if self.azure_openai:
            if not self.endpoint:
                raise ValueError("Endpoint must be set for Azure OpenAI.")
            params["azure_endpoint"] = self.endpoint
            if not self.version:
                raise ValueError("API version must be set for Azure OpenAI.")
            params["api_version"] = self.version

            embeddings = AzureOpenAIEmbeddings(**params)
        else:
            embeddings = OpenAIEmbeddings(**params)
        
        return embeddings

    @classmethod
    def create_from_env(cls) -> 'LangChainOpenAIClient':
        load_dotenv()
        props: dict = {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "azure_openai": os.getenv("AZURE_OPENAI"),
            "version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        }
        client = LangChainOpenAIClient.model_validate(props)
        return client


class LangChainVectorStore(BaseModel):
    """
    LangChain Vector Store for managing embeddings.
    This class supports Chroma as the vector store type.
    Attributes:
        vector_store_type (str): Type of vector store, currently only 'chroma' is supported.
        collection_name (str): Name of the vector store collection, defaults to "default_collection".
        folder_paths_file_path (str): Path to the JSON file containing a list of folder names, required.
        vector_store_url (str): URL for the vector store, if applicable.
        chunk_size (int): Size of chunks for text splitting, defaults to 4000.
        embedding_client (LangChainOpenAIClient): Embedding client for generating embeddings.
        use_multi_vector_retriever (bool): Flag to use MultiVectorRetriever, defaults to False.
        doc_store_url (Optional[str]): URL for the document store, if applicable.
        multi_vector_chunk_size (int): Chunk size for MultiVectorRetriever, defaults to 1000.
    """
    
    # vector store type 現在はchromaのみ対応. chroma以外はエラーを返す。defaults to chroma.
    vector_store_type: str = Field(default="chroma", description="Type of vector store, currently only 'chroma' is supported")
    # collection name defaults to "default_collection"
    collection_name: str = Field(default="default_collection", description="Name of the vector store collection")
    # folder nameのリストを格納した json file pathの文字列. 必須
    folder_paths_file_path: str = Field(..., description="Path to the JSON file containing a list of folder names")

    # vector store url for chroma
    vector_store_url: str = Field(description="URL for the vector store, if applicable")
    # chunk size for text splitting
    chunk_size: int = Field(default=4000, description="Size of chunks for text splitting")

    embedding_client: LangChainOpenAIClient = Field(..., description="Embedding client for generating embeddings")

    # Use MultiVectorRetriever for vector search
    use_multi_vector_retriever: bool = Field(default=False, description="Flag to use MultiVectorRetriever, defaults to False")
    # doc store url for MultiVectorRetriever
    doc_store_url: Optional[str] = Field(default=None, description="URL for the document store, if applicable")
    # chunk size for MultiVectorRetriever
    multi_vector_chunk_size: int = Field(default=1000, description="Chunk size for MultiVectorRetriever")

    @field_validator("vector_store_type")
    def validate_vector_store_type(cls, value: str, info: ValidationInfo) -> str:
        valid_types = ["chroma"]
        if value not in valid_types:
            raise ValueError(f"Invalid vector store type. Must be one of {valid_types}.")
        return value
    
    @classmethod
    def get_vector_store_path(cls, app_data_path: str) -> str:
        """
        アプリケーションデータパスからベクトルストアのパスを取得する。

        Args:
            app_data_path (str): アプリケーションデータのパス

        Returns:
            str: ベクトルストアのパス
        """
        return os.path.join(app_data_path, "vector_store")
    
    @classmethod
    def get_folder_paths_file_path(cls, app_data_path: str) -> str:
        """
        アプリケーションデータパスからフォルダ名のファイルパスを取得する。

        Args:
            app_data_path (str): アプリケーションデータのパス

        Returns:
            str: フォルダ名のファイルパス
        """
        return os.path.join(app_data_path, "folder_paths.json")
    

    def create_retriever(self, search_kwargs: dict[str, Any] = {}) -> "BaseRetriever":
        # ベクトルDB検索用のRetrieverオブジェクトの作成と設定

        if not search_kwargs:
            # デフォルトの検索パラメータを設定
            logger.info("search_kwargs is empty. Set default search_kwargs")
            search_kwargs = {"k": 10}
        
        vector_retriver_wrapper = VectorRetrieverWrapper(
            vectorstore=self.get_vector_store(),
            doc_id="doc_id",
            search_kwargs=search_kwargs,
            use_multi_vector_retriever=self.use_multi_vector_retriever,
            docstore=SQLDocStore(self.doc_store_url) if self.doc_store_url else None
        )
        return vector_retriver_wrapper.retriever


    def get_vector_store(self) -> VectorStore:

        # ベクトルDB用のディレクトリが存在しない場合
        if not os.path.exists(self.vector_store_url):
            # ディレクトリを作成
            os.makedirs(self.vector_store_url)
            # ディレクトリが作成されたことをログに出力
            logger.info(f"create directory:{self.vector_store_url}")
        # params
        settings = chromadb.config.Settings(anonymized_telemetry=False)

        params: dict[str, Any]= {}
        params["client"] = chromadb.PersistentClient(path=self.vector_store_url, settings=settings)
        params["embedding_function"] = self.embedding_client.get_embedding_client()
        params["collection_metadata"] = {"hnsw:space":"cosine"}
        # collectionが指定されている場合
        logger.info(f"collection_name:{self.collection_name}")
        if self.collection_name:
            params["collection_name"] = self.collection_name
                    
        db: VectorStore = Chroma(
            **params
            )
        return db


    def __load_folder_path_list(self) -> set[str]:
        # ファイルがない場合はファイルを作成
        if not os.path.exists(self.folder_paths_file_path):
            self.__save_folder_path_list(set())
            return set()

        try:
            with open(self.folder_paths_file_path, 'r', encoding='utf-8') as f:
                folder_paths = json.load(f)
            return set(folder_paths.get("folder_paths", []))  # JSONからフォルダ名のリストを取得し、setに変換
        except Exception as e:
            raise ValueError(f"Failed to load folder names from {self.folder_paths_file_path}: {e}")    
    
    def __save_folder_path_list(self, new_folder_paths: set[str]) -> None:
        # setはjsonに直接保存できないので、listに変換
        if not isinstance(new_folder_paths, set):
            raise ValueError("new_folder_paths must be a set of folder names.")
        new_folder_paths_list = list(new_folder_paths)
        # Update the folder names in the JSON file
        try:
            with open(self.folder_paths_file_path, 'w', encoding='utf-8') as f:
                json.dump({"folder_paths": new_folder_paths_list}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValueError(f"Failed to update folder names in {self.folder_paths_file_path}: {e}")

    def __update_folder_path_list(self, folder_path: str) -> None:
        # Update the folder name list with a new folder name
        folder_paths = self.__load_folder_path_list()
        folder_paths.add(folder_path)
        self.__save_folder_path_list(folder_paths)

    async def update_embeddings(
        self, 
        data_list: list[EmbeddingData]
    ) -> None:
        """
        Update the vector store with new embeddings.
        If the folder name is not in the list, it will be added.
        """
        # Load existing folder names
        existing_folders = self.__load_folder_path_list()

        for data in data_list:

            # Check if the folder name already exists
            if data.folder_path and data.folder_path not in existing_folders:
                self.__update_folder_path_list(data.folder_path)

            if data.source_path:
                # delete existing embeddings with the same source_path
                logger.info(f"Deleting existing embeddings with source_path: {data.source_path}")
                await self.get_vector_store().adelete(where={"source_path": data.source_path})
        
                # delete existing documents with the same folder_path from the document store
                if self.use_multi_vector_retriever:
                    logger.info(f"Deleting existing documents with source_path: {data.source_path}")
                    doc_ids, _ = await self.get_document_ids_by_tag(name="source_path", value=data.source_path)
                    if doc_ids:
                        await self.delete_documents_from_doc_store(doc_ids, self.doc_store_url)

        # prepare the document for embedding
        documents = self.prepare_documents(data_list)
        if not self.use_multi_vector_retriever:
            # If not using MultiVectorRetriever, we can add documents directly
            logger.info("Adding documents to the vector store")
            # Add the document to the vector store
            await self.add_doucment_with_retry(self.get_vector_store(), documents)
        else:
            # prepare sub-documents for MultiVectorRetriever
            logger.info("Preparing sub-documents for MultiVectorRetriever")
            sub_documents = self.preapre_sub_documents(documents)
            # If using MultiVectorRetriever, we need to add documents with retry logic
            logger.info("Adding documents to the vector store with retry logic")
            await self.add_doucment_with_retry(self.get_vector_store(), sub_documents)
            # Add the documents to the document store
            logger.info("Adding documents to the document store")
            await self.add_documents_to_doc_store(sub_documents, self.doc_store_url)

    def preapre_sub_documents(
        self,
        source_documents: list[Document],
    ) -> List[Document]:
        """
        Prepare sub-documents for embedding.
        This method splits the content of each document into chunks.
        """
        sub_docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.multi_vector_chunk_size, chunk_overlap=0)
        for doc in source_documents:
            doc_id = doc.metadata.get("doc_id", str(uuid.uuid4()))
            splited_docs = text_splitter.split_documents([doc])
            if len(splited_docs) == 0:
                raise ValueError("splited_docs is empty")
            for sub_doc in splited_docs:
                sub_doc.metadata["doc_id"] = doc_id
                sub_docs.append(sub_doc)

        return sub_docs
        

    def prepare_documents(
        self, 
        data_list: list[EmbeddingData],
    ) -> List[Document]:
        """
        Prepare documents for embedding.
        This method converts EmbeddingData to Document objects.
        """
        documents = []
        for data in data_list:
            # Create a Document object
            metadata = {}
            if data.folder_path:
                metadata["folder_path"] = data.folder_path
            if data.description:
                metadata["description"] = data.description
            if data.source_path:
                metadata["source_path"] = data.source_path
            # Generate a unique doc_id
            doc_id = str(uuid.uuid4())
            metadata["doc_id"] = doc_id

            # split the content into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=0)
            chunks = text_splitter.split_text(data.content)
            for chunk in chunks:
                document = Document(
                    page_content=chunk,
                    metadata=metadata
                )
                documents.append(document)

        return documents

    async def add_documents_to_doc_store(
        self,
        documents: list[Document],
        doc_store_url: Optional[str] = None
    ) -> None:
        """
        Add documents to the document store.
        This method is used to store documents in the SQLDocStore.
        """
        if not doc_store_url:
            doc_store_url = self.doc_store_url
        if not doc_store_url:
            raise ValueError("doc_store_url must be provided.")

        # Create a SQLDocStore instance
        doc_store = SQLDocStore(doc_store_url)
        
        # Add documents to the document store
        for doc in documents:
            # 元のドキュメントをDocStoreに保存
            doc_id = doc.metadata.get("doc_id", None)
            if not doc_id:
                raise ValueError("Document must have a 'doc_id' in metadata.")
            param = []
            param.append((doc_id, doc))
            await doc_store.amset(param)

    async def delete_documents_from_doc_store(
        self,
        doc_ids: List[str],
        doc_store_url: Optional[str] = None
    ) -> None:
        """
        Delete documents from the document store.
        This method is used to remove documents from the SQLDocStore.
        """
        if not doc_store_url:
            doc_store_url = self.doc_store_url
        if not doc_store_url:
            raise ValueError("doc_store_url must be provided.")

        # Create a SQLDocStore instance
        doc_store = SQLDocStore(doc_store_url)

        # Delete documents from the document store
        await doc_store.amdelete(doc_ids)

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

    async def get_document_ids_by_tag(self, name:str="", value:str="") -> Tuple[List, List]:
        ids=[]
        metadata_list = []
        # Get documents from the vector store by tag. if get attribute is nothing, return empty list
        vector_store = self.get_vector_store()
        # check get method is available
        if not hasattr(vector_store, "get"):
            raise ValueError("Vector store does not support 'get' method. Please check the vector store type.")

        doc_dict = vector_store.get(where={name: value}) # type: ignore

        # デバッグ用
        logger.debug("_get_document_ids_by_tag doc_dict:", doc_dict)

        # vector idを取得してidsに追加
        ids.extend(doc_dict.get("ids", []))
        metadata_list.extend(doc_dict.get("metadata", []))

        return ids, metadata_list

    async def delete_embedding_by_tag(
        self, 
        tag: str,
        value: str
    ) -> None:
        """
        Delete embeddings associated with a specific folder name.
        """

        if tag == "folder_path":
            # Load existing folder names
            existing_folders = self.__load_folder_path_list()
            existing_folders.discard(value)  # Remove the folder name if it exists
            self.__save_folder_path_list(existing_folders)  # Save the updated folder names

        # Delete documents with the specified tag and value
        await self.get_vector_store().adelete(where={ tag: value})

    async def vector_search(
        self, 
        query: str, 
        num_results: int = 5,
        score_threshold: Optional[float] = None,
        folder_path: Optional[str] = None
    ) -> List[EmbeddingData]:
        """
        Perform a vector search in the vector store.
        Returns a list of Document objects.
        """
        if not query:
            raise ValueError("Query must be provided for vector search.")
        # Perform the similarity search
        search_kwargs: Dict[str, Any] = {"k": num_results}
        if score_threshold is not None:
            search_kwargs["score_threshold"] = score_threshold
        if folder_path is not None:      
            search_kwargs["filter"] = {"folder_path": folder_path}
        # create a retriever with the search parameters
        retriever = self.create_retriever(search_kwargs=search_kwargs)
        results = await retriever.ainvoke(query, run_manager=None)

        # Document objects to EmbeddingData objects
        embedding_data_list = []
        for doc in results:
            embedding_data = EmbeddingData(
                content=doc.page_content,
                description=doc.metadata.get("description", ""),
                source_path=doc.metadata.get("source_path", None),
                folder_path=doc.metadata.get("folder_path", None)
            )
            embedding_data_list.append(embedding_data)

        return embedding_data_list
