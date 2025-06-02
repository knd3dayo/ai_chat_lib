import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List, Dict, Any, Union

from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from langchain_core.vectorstores import VectorStore # type: ignore

import chromadb
import chromadb.config
from langchain_chroma.vectorstores import Chroma # type: ignore
from langchain.docstore.document import Document

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
        folder_names_file_path (str): Path to the JSON file containing a list of folder names, required.
        vector_store_url (str): URL for the vector store, if applicable.
        embedding_client (LangChainOpenAIClient): Embedding client for generating embeddings.
    """
    
    # vector store type 現在はchromaのみ対応. chroma以外はエラーを返す。defaults to chroma.
    vector_store_type: str = Field(default="chroma", description="Type of vector store, currently only 'chroma' is supported")
    # collection name defaults to "default_collection"
    collection_name: str = Field(default="default_collection", description="Name of the vector store collection")
    # folder nameのリストを格納した json file pathの文字列. 必須
    folder_names_file_path: str = Field(..., description="Path to the JSON file containing a list of folder names")

    # vector store url for chroma
    vector_store_url: str = Field(description="URL for the vector store, if applicable")

    embedding_client: LangChainOpenAIClient = Field(..., description="Embedding client for generating embeddings")

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
    def get_folder_names_file_path(cls, app_data_path: str) -> str:
        """
        アプリケーションデータパスからフォルダ名のファイルパスを取得する。

        Args:
            app_data_path (str): アプリケーションデータのパス

        Returns:
            str: フォルダ名のファイルパス
        """
        return os.path.join(app_data_path, "folder_names.json")
    


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


    def __load_folder_name_list(self) -> set[str]:
        # ファイルがない場合はファイルを作成
        if not os.path.exists(self.folder_names_file_path):
            self.__save_folder_name_list(set())
            return set()

        try:
            with open(self.folder_names_file_path, 'r', encoding='utf-8') as f:
                folder_names = json.load(f)
            return set(folder_names.get("folder_names", []))  # JSONからフォルダ名のリストを取得し、setに変換
        except Exception as e:
            raise ValueError(f"Failed to load folder names from {self.folder_names_file_path}: {e}")    
    
    def __save_folder_name_list(self, new_folder_names: set[str]) -> None:
        # setはjsonに直接保存できないので、listに変換
        if not isinstance(new_folder_names, set):
            raise ValueError("new_folder_names must be a set of folder names.")
        new_folder_names_list = list(new_folder_names)
        # Update the folder names in the JSON file
        try:
            with open(self.folder_names_file_path, 'w', encoding='utf-8') as f:
                json.dump({"folder_names": new_folder_names_list}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValueError(f"Failed to update folder names in {self.folder_names_file_path}: {e}")

    def __update_folder_name_list(self, folder_name: str) -> None:
        # Update the folder name list with a new folder name
        folder_names = self.__load_folder_name_list()
        folder_names.add(folder_name)
        self.__save_folder_name_list(folder_names)

    def update_embeddings(
        self, 
        data_list: list[EmbeddingData]
    ) -> None:
        """
        Update the vector store with new embeddings.
        If the folder name is not in the list, it will be added.
        """
        # Load existing folder names
        existing_folders = self.__load_folder_name_list()

        documents = []
        for data in data_list:

            # Check if the folder name already exists
            if data.folder_path and data.folder_path not in existing_folders:
                self.__update_folder_name_list(data.folder_path)

            # Create a Document object
            metadata = {}
            if data.folder_path:
                metadata["folder_name"] = data.folder_path
            if data.description:
                metadata["description"] = data.description
            if data.source_path:
                metadata["source_path"] = data.source_path

            document = Document(
                page_content=data.content,
                metadata=metadata
            )
            documents.append(document)

        # Add the document to the vector store
        self.get_vector_store().add_documents(documents)

    def delete_embedding(
        self, 
        folder_name: str
    ) -> None:
        """
        Delete embeddings associated with a specific folder name.
        """
        # Load existing folder names
        existing_folders = self.__load_folder_name_list()

        # Check if the folder name exists
        if folder_name not in existing_folders:
            raise ValueError(f"Folder name '{folder_name}' does not exist in the vector store.")

        # Delete documents with the specified folder name
        self.get_vector_store().delete(where={"folder_name": folder_name})

    def vector_search(
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
            search_kwargs["filter"] = {"folder_name": folder_path}
        results = self.get_vector_store().similarity_search(query,search_kwargs=search_kwargs)
        # Document objects to EmbeddingData objects
        embedding_data_list = []
        for doc in results:
            embedding_data = EmbeddingData(
                content=doc.page_content,
                description=doc.metadata.get("description", ""),
                source_path=doc.metadata.get("source_path", None),
                folder_path=doc.metadata.get("folder_name", None)
            )
            embedding_data_list.append(embedding_data)

        return embedding_data_list
