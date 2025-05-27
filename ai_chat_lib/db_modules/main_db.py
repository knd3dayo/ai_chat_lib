import sqlite3
import json
from typing import List, Union, Optional, ClassVar
import uuid
import os
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from typing import Optional, List
from typing import Optional
from typing import Optional, Union, List
from typing import Optional, List, Dict, Any, Union

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)
class ContentFoldersCatalog(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "ContentFoldersCatalog" (
        "id" TEXT NOT NULL CONSTRAINT "PK_ContentFoldersCatalog" PRIMARY KEY,
        "folder_type_string" TEXT NOT NULL,
        "parent_id" TEXT NULL,
        "folder_name" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "extended_properties_json" TEXT NOT NULL,
        "is_root_folder" INTEGER NOT NULL
    )
    '''
    id: Optional[str] = None
    folder_type_string: Optional[str] = None
    parent_id: Optional[str] = None
    folder_name: Optional[str] = None
    description: Optional[str] = None
    extended_properties_json: Optional[str] = None
    folder_path: Optional[str] = None
    is_root_folder: bool = False

    get_content_folder_requests_name: ClassVar[str] = "content_folder_requests"

    @field_validator("is_root_folder", mode="before")
    @classmethod
    def parse_is_root_folder(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @classmethod
    def get_content_folder_request_objects(cls, request_dict: dict) -> List["ContentFoldersCatalog"]:
        '''
        {"content_folder_requests": [] }の形式で渡される
        '''
        content_folders = request_dict.get(cls.get_content_folder_requests_name, None)
        if not content_folders:
            raise ValueError("content_folder is not set.")
        return [cls(**item) for item in content_folders]

    @classmethod
    def get_root_content_folders_api(cls):
        main_db = MainDB()
        content_folders = main_db.get_root_content_folders()
        result = {}
        result["content_folders"] = [item.to_dict() for item in content_folders]
        return result

    @classmethod
    def get_content_folders_api(cls):
        main_db = MainDB()
        content_folders = main_db.get_content_folders()
        result = {}
        result["content_folders"] = [item.to_dict() for item in content_folders]
        return result

    @classmethod
    def get_content_folder_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_id = cls.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        main_db = MainDB()
        content_folder = main_db.get_content_folder_by_id(content_folder_id)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] = content_folder.to_dict()
        return result

    @classmethod
    def update_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = cls.get_content_folder_request_objects(request_dict)
        main_db = MainDB()
        for content_folder in content_folders:
            main_db.update_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    def delete_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = cls.get_content_folder_request_objects(request_dict)
        main_db = MainDB()
        for content_folder in content_folders:
            main_db.delete_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    def get_content_folder_by_path_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_path = request_dict.get("content_folder_path", None)
        if not content_folder_path:
            raise ValueError("content_folder_path is not set")
        main_db = MainDB()
        content_folder = main_db.get_content_folder_by_path(content_folder_path)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] = content_folder.to_dict()
        return result

    @classmethod
    def get_content_folder_path_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_id = cls.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        main_db = MainDB()
        content_folder_path = main_db.get_content_folder_path_by_id(content_folder_id)
        result: dict = {}
        if content_folder_path is not None:
            result["content_folder_path"] = content_folder_path
        return result

    def to_dict(self) -> dict:
        result = self.model_dump()
        # folder_pathがなければidから取得
        if not result.get("folder_path") and self.id:
            main_db = MainDB()
            content_folder_path = main_db.get_content_folder_path_by_id(self.id)
            if content_folder_path:
                result["folder_path"] = content_folder_path
        return result

class VectorDBItem(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "VectorDBItems" (
        "id" TEXT NOT NULL CONSTRAINT "PK_VectorDBItems" PRIMARY KEY,
        "name" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "vector_db_url" TEXT NOT NULL,
        "is_use_multi_vector_retriever" INTEGER NOT NULL,
        "doc_store_url" TEXT NOT NULL,
        "vector_db_type" INTEGER NOT NULL,
        "collection_name" TEXT NOT NULL,
        "chunk_size" INTEGER NOT NULL,
        "default_search_result_limit" INTEGER NOT NULL,
        "is_enabled" INTEGER NOT NULL,
        "is_system" INTEGER NOT NULL
    )    
    '''
    # コレクションの指定がない場合はデフォルトのコレクション名を使用
    DEFAULT_COLLECTION_NAME: ClassVar[str] = "ai_app_default_collection"
    FOLDER_CATALOG_COLLECTION_NAME: ClassVar[str] = "ai_app_folder_catalog_collection"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    vector_db_url: str
    is_use_multi_vector_retriever: bool = False
    doc_store_url: str
    collection_name: str = DEFAULT_COLLECTION_NAME
    chunk_size: int = 0
    default_search_result_limit: int = 10
    default_score_threshold: float = 0.5
    is_enabled: bool = False
    is_system: bool = False
    vector_db_type: int = Field(default=0, ge=0, le=2, description="0: Chroma, 1: PGVector, 2: Other")
    system_message: Optional[str] = None
    folder_id: Optional[str] = ""

    @field_validator("is_use_multi_vector_retriever")
    @classmethod
    def parse_bool_multi_vector(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @field_validator("is_enabled")
    @classmethod
    def parse_bool_enabled(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @field_validator("is_system")
    @classmethod
    def parse_bool_system(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @field_validator("system_message")
    @classmethod
    def parse_system_message(cls, v, values):
        if v:
            return v
        return values.get("description", "")

    @classmethod
    def update_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = VectorDBItem.get_vector_db_item_object(request_dict)
        main_db = MainDB()
        main_db.update_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    def delete_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = VectorDBItem.get_vector_db_item_object(request_dict)
        main_db = MainDB()
        main_db.delete_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    def get_vector_db_items_api(cls):
        main_db = MainDB()
        vector_db_list = main_db.get_vector_db_items()
        result = {}
        result["vector_db_items"] = [item.to_dict() for item in vector_db_list]
        return result

    @classmethod
    def get_vector_db_item_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_id = VectorDBItem.get_vector_db_item_object(request_dict).id
        if not vector_db_id:
            raise ValueError("vector_db_id is not set")
        main_db = MainDB()
        vector_db_item = main_db.get_vector_db_by_id(vector_db_id)
        result: dict = {}
        if vector_db_item is not None:
            result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    def get_vector_db_item_by_name_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_name = VectorDBItem.get_vector_db_item_object(request_dict).name
        if not vector_db_name:
            raise ValueError("vector_db_name is not set")
        main_db = MainDB()
        vector_db = main_db.get_vector_db_by_name(vector_db_name)
        result: dict = {}
        if vector_db is not None:
            result["vector_db_item"] = vector_db.to_dict()
        return result

    vector_db_item_request_name: ClassVar[str] = "vector_db_item_request"

    @classmethod
    def get_vector_db_item_object(cls, request_dict: dict) -> "VectorDBItem":
        vector_db_item_request = request_dict.get(cls.vector_db_item_request_name, None)
        if not vector_db_item_request:
            raise ValueError("vector_db_item_request is not set.")
        return VectorDBItem(**vector_db_item_request)

    def to_dict(self) -> dict:
        return self.model_dump()
    
    def get_vector_db_type_string(self) -> str:
        '''
        vector_db_typeを文字列で返す
        '''
        if self.vector_db_type == 0:
            return "Chroma"
        elif self.vector_db_type == 1:
            return "PGVector"
        elif self.vector_db_type == 2:
            return "Other"
        else:
            return "Unknown"

class VectorSearchRequest(BaseModel):
    name: str = ""
    query: str = ""
    model: str = ""
    search_kwargs: Dict[str, Any] = Field(default_factory=dict)
    vector_db_item: Optional["VectorDBItem"] = None

    vector_search_requests_name: ClassVar[str] = "vector_search_requests"

    @classmethod
    def get_vector_search_requests_objects(cls, request_dict: dict) -> List["VectorSearchRequest"]:
        '''
        {"vector_search_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[List[dict], None] = request_dict.get(cls.vector_search_requests_name, None)
        if not request:
            logger.info("vector search request is not set. skipping.")
            return []
        vector_search_requests = []
        for item in request:
            vector_search_request = VectorSearchRequest(**item)
            # search_kwargsのアップデート
            vector_search_request.search_kwargs = vector_search_request.__update_search_kwargs(vector_search_request.search_kwargs)
            vector_search_requests.append(vector_search_request)
        return vector_search_requests

    def __update_search_kwargs(self, kwargs: dict) -> dict:
        filter = kwargs.get("filter", None)
        if not filter:
            logger.debug("__update_search_kwargs: filter is not set.")
            return kwargs
        folder_path = filter.get("folder_path", None)
        if folder_path:
            logger.info(f"__update_search_kwargs: folder_path: {folder_path}")
            main_db = MainDB()
            temp_folder = main_db.get_content_folder_by_path(folder_path)
            if temp_folder and temp_folder.id:
                kwargs["filter"]["folder_id"] = temp_folder.id
            kwargs["filter"].pop("folder_path", None)
        else:
            logger.info("__update_search_kwargs: folder_path is not set.")
        return kwargs

    def get_vector_db_item(self) -> "VectorDBItem":
        if self.vector_db_item:
            return self.vector_db_item
        main_db = MainDB()
        vector_db_item = main_db.get_vector_db_by_name(self.name)
        if not vector_db_item:
            raise ValueError("VectorDBItem is not found.")
        return vector_db_item

    def to_dict(self) -> dict:
        return self.model_dump()

class EmbeddingData(BaseModel):
    name: str
    model: str
    source_id: str
    folder_id: str 
    description: str = ""
    content: str
    source_path: str = ""
    git_repository_url: str = ""
    git_relative_path: str = ""
    image_url: str = ""

    embedding_request_name: ClassVar[str] = "embedding_request"

    @classmethod
    def get_embedding_request_objects(cls, request_dict: dict) -> "EmbeddingData":
        '''
        {"embedding_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.embedding_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return EmbeddingData(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

class TagItem(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "TagItems" (
    "id" TEXT NOT NULL CONSTRAINT "PK_TagItems" PRIMARY KEY,
    "tag" TEXT NOT NULL,
    "is_pinned" INTEGER NOT NULL
    )
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tag: str
    is_pinned: bool = False

    @field_validator("is_pinned")
    @classmethod
    def parse_is_pinned(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @classmethod
    def get_tag_item_objects(cls, request_dict: dict) -> List["TagItem"]:
        '''
        {"tag_item_requests": []}の形式で渡される
        '''
        tag_items: Optional[List[dict]] = request_dict.get("tag_item_requests", None)
        if not tag_items:
            raise ValueError("tag_items is not set.")
        return [cls(**item) for item in tag_items]

    @classmethod
    def get_tag_items_api(cls, request_json: str):
        main_db = MainDB()
        tag_items = main_db.get_tag_items()
        result: dict = {}
        result["tag_items"] = [item.dict() for item in tag_items]
        return result

    @classmethod
    def update_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = TagItem.get_tag_item_objects(request_dict)
        main_db = MainDB()
        for tag_item in tag_items:
            main_db.update_tag_item(tag_item)
        result: dict = {}
        return result

    @classmethod
    def delete_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = TagItem.get_tag_item_objects(request_dict)
        main_db = MainDB()
        for tag_item in tag_items:
            main_db.delete_tag_item(tag_item)
        result: dict = {}
        return result

    def to_dict(self) -> dict:
        return self.dict()

class AutogentLLMConfig(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_llm_configs (name TEXT, api_type TEXT, api_version TEXT, model TEXT, api_key TEXT, base_url TEXT)
    '''
    name: str = ""
    api_type: str = ""
    api_version: str = ""
    model: str = ""
    api_key: str = ""
    base_url: str = ""

    @classmethod
    def get_autogen_llm_config_list_api(cls):
        main_db = MainDB()
        llm_config_list = main_db.get_autogen_llm_config_list()
        if not llm_config_list:
            raise ValueError("llm_config_list is not set")
        result = {}
        result["llm_config_list"] = [config.to_dict() for config in llm_config_list]
        return result

    @classmethod
    def get_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogentLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        main_db = MainDB()
        llm_config_result = main_db.get_autogen_llm_config(llm_config.name)
        result: dict = {}
        if llm_config_result:
            result["llm_config"] = llm_config_result.to_dict()
        return result

    @classmethod
    def update_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogentLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        main_db = MainDB()
        main_db.update_autogen_llm_config(llm_config)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogentLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        main_db = MainDB()
        main_db.delete_autogen_llm_config(llm_config)
        result: dict = {}
        return result

    autogen_llm_config_request_name: ClassVar[str] = "autogen_llm_config_request"

    @classmethod
    def get_autogen_llm_config_object(cls, request_dict: dict) -> "AutogentLLMConfig":
        request: Optional[dict] = request_dict.get(cls.autogen_llm_config_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogentLLMConfig(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

class AutogenTools(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_tools (name TEXT, path TEXT, description TEXT)
    '''
    name: str = ""
    path: str = ""
    description: str = ""

    @classmethod
    def get_autogen_tool_list_api(cls):
        main_db = MainDB()
        tools_list = main_db.get_autogen_tool_list()
        result = {}
        result["tool_list"] = [tool.to_dict() for tool in tools_list]
        return result

    @classmethod
    def get_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        main_db = MainDB()
        tool_result = main_db.get_autogen_tool(tool.name)
        result: dict = {}
        if tool_result:
            result["tool"] = tool_result.to_dict()
        return result

    @classmethod
    def update_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        main_db = MainDB()
        main_db.update_autogen_tool(tool)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        main_db = MainDB()
        main_db.delete_autogen_tool(tool)
        result: dict = {}
        return result

    autogen_tool_request_name: ClassVar[str] = "autogen_tool_request"

    @classmethod
    def get_autogen_tool_object(cls, request_dict: dict) -> "AutogenTools":
        '''
        {"autogen_tool_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.autogen_tool_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenTools(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

class AutogenAgent(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_agents (
        name TEXT PRIMARY KEY, description TEXT, system_message TEXT, 
        code_execution INTEGER, llm_config_name TEXT, tool_names_json TEXT, vector_db_items_json TEXT)
    '''
    name: str = ""
    description: str = ""
    system_message: str = ""
    code_execution: bool = False
    llm_config_name: str = ""
    tool_names: Union[str, list, None] = ""
    vector_db_items: Union[list, None] = []
    tool_names_json: Optional[str] = None
    vector_db_items_json: Optional[str] = None

    @field_validator("code_execution", mode="before")
    @classmethod
    def parse_code_execution(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @field_validator("tool_names", mode="before")
    @classmethod
    def parse_tool_names(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("tool_names_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return ""

    @field_validator("vector_db_items", mode="before")
    @classmethod
    def parse_vector_db_items(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("vector_db_items_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return []

    @classmethod
    def get_autogen_agent_list_api(cls):
        main_db = MainDB()
        agent_list = main_db.get_autogen_agent_list()
        if not agent_list:
            raise ValueError("agent_list is not set")
        result = {}
        result["agent_list"] = [agent.to_dict() for agent in agent_list]
        return result

    @classmethod
    def get_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        main_db = MainDB()
        agent_result = main_db.get_autogen_agent(agent.name)
        result: dict = {}
        if agent_result:
            result["agent"] = agent_result.to_dict()
        return result

    @classmethod
    def update_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        main_db = MainDB()
        main_db.update_autogen_agent(agent)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        main_db = MainDB()
        main_db.delete_autogen_agent(agent)
        result: dict = {}
        return result

    autogen_agent_request_name: ClassVar[str] = "autogen_agent_request"

    @classmethod
    def get_autogen_agent_object(cls, request_dict: dict) -> "AutogenAgent":
        request: Optional[dict] = request_dict.get(cls.autogen_agent_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenAgent(**request)

    def to_dict(self) -> dict:
        return self.model_dump()
    
class AutogenGroupChat(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_group_chats (name TEXT, description TEXT, llm_config_name TEXT, agent_names_json TEXT)
    '''
    name: str = ""
    description: str = ""
    llm_config_name: str = ""
    agent_names: list = Field(default_factory=list)
    agent_names_json: Optional[str] = None

    @field_validator("agent_names", mode="before")
    @classmethod
    def parse_agent_names(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("agent_names_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return []

    @classmethod
    def get_autogen_group_chat_list_api(cls):
        main_db = MainDB()
        group_chat_list = main_db.get_autogen_group_chat_list()
        if not group_chat_list:
            raise ValueError("group_chat_list is not set")
        result = {}
        result["group_chat_list"] = [group_chat.to_dict() for group_chat in group_chat_list]
        return result

    autogen_group_chat_request_name: ClassVar[str] = "autogen_group_chat_request"

    @classmethod
    def get_autogen_group_chat_object(cls, request_dict: dict) -> "AutogenGroupChat":
        request: Optional[dict] = request_dict.get(cls.autogen_group_chat_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenGroupChat(**request)

    @classmethod
    def get_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        main_db = MainDB()
        group_chat_result = main_db.get_autogen_group_chat(group_chat.name)
        result: dict = {}
        if group_chat_result:
            result["group_chat"] = group_chat_result.to_dict()
        return result

    @classmethod
    def update_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        main_db = MainDB()
        main_db.update_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        main_db = MainDB()
        main_db.delete_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    def to_dict(self) -> dict:
        return self.model_dump()

class MainDB:

    @classmethod
    def init(cls, upgrade: bool = False):
        # main_dbへのパスを取得
        app_db_path = MainDB.get_main_db_path()
        cls.__init_database(app_db_path, upgrade)

    # main_dbへのパスを取得
    @classmethod
    def get_main_db_path(cls) -> str:
        app_data_path = os.getenv("APP_DATA_PATH", None)
        if not app_data_path:
            raise ValueError("APP_DATA_PATH is not set.")
        app_db_path = os.path.join(app_data_path, "server", "main_db", "server_main.db")

        return app_db_path

    @classmethod
    def __init_database(cls, app_db_path: str, upgrade: bool = False):

        # db_pathが存在しない場合は作成する
        if not os.path.exists(app_db_path):
            os.makedirs(os.path.dirname(app_db_path), exist_ok=True)
            conn = sqlite3.connect(app_db_path)
            conn.close()
            # データベースの初期化
            main_db = MainDB(app_db_path)
            # テーブルの初期化
            cls.__init_tables(main_db)

        if upgrade:
            main_db = MainDB(app_db_path)
            # DBのアップグレード処理
            cls.__update_database(main_db)

    @classmethod
    def __init_tables(cls, main_db: "MainDB"):
        # DBPropertiesテーブルを初期化
        main_db.init_db_properties_table()
        # ContentFoldersテーブルを初期化
        main_db.__init_content_folder_catalog_table()
        # ContentFoldersCatalogにindexを追加
        main_db.__init_content_folder_catalog_index()
        # TagItemsテーブルを初期化
        main_db.__init_tag_item_table()
        # VectorDBItemsテーブルを初期化
        main_db.__init_vector_db_item_table()
        # autogen_llm_configsテーブルを初期化
        main_db.__init_autogen_llm_config_table()
        # autogen_toolsテーブルを初期化
        main_db.__init_autogen_tools_table()
        # autogen_agentsテーブルを初期化
        main_db.__init_autogen_agents_table()
        # autogen_group_chatsテーブルを初期化
        main_db.__init_autogen_group_chats_table()

    @classmethod
    def __update_database(cls, db: "MainDB"):
        # DBのアップグレード処理
        pass

    @classmethod
    def __create_update_sql(cls, table_name: str, key: str, items: dict ) -> str:
        # itemsからkeyをpopする
        if key not in items:
            raise ValueError(f"{key} is not in items.")
        # itemsからkeyをpopする
        key_value = items.pop(key)
        key_str = ""
        if type(key_value) == str:
            key_str = f"{key} = '{key_value}'"
        else:
            key_str = f"{key} = {key_value}"

        # itemsの値を文字列に変換する
        items_str = ""
        for k, v in items.items():
            # Noneの場合はスキップ
            if v is None:
                continue
            if type(v) == str:
                items_str += f"{k} = '{v}', "
            else:
                items_str += f"{k} = {v}, "
        # itemsの最後のカンマを削除する
        items_str = items_str[:-2]
        # SQL文を生成する
        sql = f"UPDATE {table_name} SET {items_str} WHERE {key_str}"
        return sql
    
    @classmethod
    def __create_insert_sql(cls, table_name: str, items: dict) -> str:
        insert_str = ""
        for k, v in items.items():
            if type(v) == str:
                insert_str += f"{k} = '{v}', "
            else:
                insert_str += f"{k} = {v}, "
        # itemsの最後のカンマを削除する
        items_str = insert_str[:-2]
        # SQL文を生成する
        sql = f"INSERT INTO {table_name} SET {items_str}"
        return sql
    

    def __init__(self, db_path = ""):
        # db_pathが指定されている場合は、指定されたパスを使用する
        if db_path:
            self.db_path = db_path
        else:
            # db_pathが指定されていない場合は、環境変数から取得する
            self.db_path = MainDB.get_main_db_path()

        # データベースの初期化
        MainDB.__init_database(self.db_path)

    def init_db_properties_table(self):
        # DBPropertiesテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS DBProperties (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                value TEXT NOT NULL
            )
        ''')
        # version = 1を追加
        cur.execute('''
            INSERT OR IGNORE INTO DBProperties (id, name, value) VALUES (?, ?, ?)
        ''', (str(uuid.uuid4()), "version", "1"))

        conn.commit()
        conn.close()

    def __init_content_folder_catalog_table(self):
        # ContentFoldersテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ContentFoldersCatalog (
                id TEXT NOT NULL PRIMARY KEY,
                folder_type_string TEXT NOT NULL,
                parent_id TEXT NULL,
                folder_name TEXT NOT NULL,
                description TEXT NOT NULL,
                extended_properties_json TEXT NOT NULL,
                is_root_folder INTEGER NOT NULL DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

    def __init_content_folder_catalog_index(self):
        # parent_idにインデックスを追加

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_parent_id ON ContentFoldersCatalog (parent_id)
        ''')
        # folder_nameにインデックスを追加
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_folder_name ON ContentFoldersCatalog (folder_name)
        ''')

        conn.commit()
        conn.close()

    def __init_tag_item_table(self):
        # TagItemsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS TagItems (
                id TEXT NOT NULL PRIMARY KEY,
                tag TEXT NOT NULL,
                is_pinned INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def __init_vector_db_item_table(self):
        # VectorDBItemsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS VectorDBItems (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                vector_db_url TEXT NOT NULL,
                is_use_multi_vector_retriever INTEGER NOT NULL,
                doc_store_url TEXT NOT NULL,
                vector_db_type INTEGER NOT NULL,
                collection_name TEXT NOT NULL,
                chunk_size INTEGER NOT NULL,
                default_search_result_limit INTEGER NOT NULL,
                default_score_threshold REAL NOT NULL DEFAULT 0.5,
                is_enabled INTEGER NOT NULL,
                is_system INTEGER NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        self.__init_default_vector_db_item()

    def __init_default_vector_db_item(self):
        # name="default"のVectorDBItemを取得
        vector_db_item = self.get_vector_db_by_name("default")
        # 存在しない場合は初期化処理
        if not vector_db_item:
            # VectorDBItemを作成
            params = {
                "name": "default",
                "description": "Application default vector db",
                "vector_db_url": os.path.join(os.getenv("APP_DATA_PATH", ""), "server", "vector_db", "default_vector_db"),
                "is_use_multi_vector_retriever": True,
                "doc_store_url": f'sqlite:///{os.path.join(os.getenv("APP_DATA_PATH", ""), "server", "vector_db", "default_doc_store.db")}',
                "vector_db_type": 1,
                "collection_name": "ai_app_default_collection",
                "chunk_size": 4096,
                "default_search_result_limit": 10,
                "is_enable": True,
                "is_system": False,
            }
            vector_db_item = VectorDBItem(**params)
            # VectorDBItemのプロパティを設定

            # MainDBに追加
            self.update_vector_db_item(vector_db_item)

        else:
            # 存在する場合は初期化処理を行わない
            logger.info("VectorDBItem is already exists.")

    def __init_autogen_llm_config_table(self):
        # autogen_llm_configsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_llm_configs (
                name TEXT PRIMARY KEY,
                api_type TEXT,
                api_version TEXT,
                model TEXT,
                api_key TEXT,
                base_url TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def __init_autogen_tools_table(self):
        # autogen_toolsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_tools (
                name TEXT PRIMARY KEY,
                path TEXT,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def __init_autogen_agents_table(self):
        # autogen_agentsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_agents (
                name TEXT PRIMARY KEY,
                description TEXT,
                system_message TEXT,
                code_execution INTEGER,
                llm_config_name TEXT,
                tool_names_json TEXT,
                vector_db_items_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    def __init_autogen_group_chats_table(self):
        # autogen_group_chatsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_group_chats (
                name TEXT PRIMARY KEY,
                description TEXT,
                llm_config_name TEXT,
                agent_names_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    #########################################
    # DBProperties関連
    #########################################
    def get_db_properties(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM DBProperties")
        rows = cur.fetchall()
        db_properties = {row["name"]: row["value"] for row in rows}
        conn.close()

        return db_properties
    
    def get_db_property(self, name: str) -> Union[str, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM DBProperties WHERE name=?", (name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        db_property_dict = dict(row)
        conn.close()

        return db_property_dict["value"]
    
    def update_db_property(self, name: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_db_property(name) is None:
            cur.execute("INSERT INTO DBProperties (id, name, value) VALUES (?, ?, ?)", (str(uuid.uuid4()), name, value))
        else:
            cur.execute("UPDATE DBProperties SET value=? WHERE name=?", (value, name))
        conn.commit()
        conn.close()

    def delete_db_property(self, name: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM DBProperties WHERE name=?", (name,))
        conn.commit()
        conn.close()


    #########################################
    # ContentFolder関連
    #########################################
    # idを指定して、idとfolder_nameとparent_idを取得する.再帰的に親フォルダを辿り、folderのパスを生成する
    def get_content_folder_path_by_id(self, folder_id: str) -> Union[str, None]:

        def get_folder_name_recursively(folder_id: str, paths: list[str]) -> list[str]:
            # データベースへ接続
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM ContentFoldersCatalog WHERE id=?", (folder_id,))
                row = cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None:
                    logger.info(f"Folder with id {folder_id} not found.")
                    return paths
                
                logger.info(f"Folder with id {folder_id} found.")

                folder_dict = dict(row)
                folder_name = folder_dict.get("folder_name", "")
                parent_id = folder_dict.get("parent_id", "")

                logger.info(f"Folder name: {folder_name}, Parent id: {parent_id}")
                paths.append(folder_name)

                # 親フォルダが存在する場合は再帰的に取得する
                if parent_id:
                    paths = get_folder_name_recursively(parent_id, paths)

            return paths

        # フォルダのパスを取得する
        paths = get_folder_name_recursively(folder_id, [])
        if len(paths) == 0:
            logger.info(f"Folder with id {folder_id} not found.")
            return None
        # フォルダのパスを生成する
        folder_path = "/".join(reversed(paths))
        logger.info(f"get_content_folder_path_by_id: Folder path: {folder_path}")
        return folder_path

    # pathを指定して、pathにマッチするエントリーを再帰的に辿り、folderを取得する
    def get_content_folder_by_path(self, folder_path: str) -> Union[ContentFoldersCatalog, None]:
        # フォルダのパスを分割する
        folder_names = folder_path.split("/")
        # ルートフォルダから順次フォルダ名を取得する
        folder_id = None
        for folder_name in folder_names:
            # データベースへ接続
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # folder_idがNoneの場合は、ルートフォルダを取得する
                if folder_id is None:
                    cur.execute("SELECT * FROM ContentFoldersCatalog WHERE folder_name=? AND parent_id IS NULL", (folder_name,))
                else:
                    cur.execute("SELECT * FROM ContentFoldersCatalog WHERE folder_name=? AND parent_id=?", (folder_name, folder_id))
                row = cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None:
                    logger.info(f"Folder with name {folder_name} not found in parent id {folder_id}.")
                    return None
                logger.info(f"Folder with name {folder_name} found in parent id {folder_id}.")

                folder_dict = dict(row)
                folder_id = folder_dict.get("id", "")

        return self.get_content_folder_by_id(folder_id)

    def get_root_content_folders(self) -> list[ContentFoldersCatalog]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id IS NULL")
        rows = cur.fetchall()
        root_folders = [ContentFoldersCatalog(**dict(row)) for row in rows]
        conn.close()
        return root_folders
    
    def get_content_folders(self) -> List[ContentFoldersCatalog]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM ContentFoldersCatalog")
        rows = cur.fetchall()
        folders = [ContentFoldersCatalog(**dict(row)) for row in rows]
        conn.close()

        return folders

    def get_content_folder_by_id(self, folder_id: Union[str, None]) -> Union[ContentFoldersCatalog, None]:
        if folder_id is None:
            return None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM ContentFoldersCatalog WHERE id=?", (folder_id,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        folder_dict = dict(row)
        conn.close()

        return ContentFoldersCatalog(**folder_dict)

    def update_content_folder(self, folder: ContentFoldersCatalog):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        id = None
        if folder.id:
            folder_id_folder = self.get_content_folder_by_id(folder.id)
            if folder_id_folder:
                id = folder_id_folder.id
        # folder_pathが指定されている場合は、folder_pathからFolderを取得する
        elif folder.folder_path:
            folder_path_folder = self.get_content_folder_by_path(folder.folder_path)
            if folder_path_folder:
                id = folder_path_folder.id

        if id is None:
            logger.info(f"ContentFolder {folder.folder_name} is not exists. Create new folder.")
            if not folder.id:
                folder.id = str(uuid.uuid4())
            sql = f"INSERT INTO ContentFoldersCatalog (id, folder_type_string, parent_id, folder_name, description, extended_properties_json) VALUES (?, ?, ?, ?, ?, ?)"
            logger.info(f"SQL: {sql}")
            insert_params = (folder.id, folder.folder_type_string, folder.parent_id, folder.folder_name, folder.description, folder.extended_properties_json)
            logger.info(f"Params: {insert_params}")
            cur.execute(sql , insert_params)
        else:
            # idが存在する場合は、更新処理を行う
            folder.id = id
            update_params = folder.to_dict()
            # folder_pathは、ContentFoldersCatalogのテーブルには存在しないので、リセットする
            update_params["folder_path"] = None

            folder.folder_path = None
            logger.info(f"ContentFolder {folder.folder_name} is exists. Update folder.")
            sql = MainDB.__create_update_sql("ContentFoldersCatalog", "id", update_params)
            logger.info(f"SQL: {sql}")
            cur.execute(sql)

        conn.commit()
        conn.close()

    def update_content_folder_by_path(self, folder: ContentFoldersCatalog):        
        folder_path = folder.folder_path
        if not folder_path:
            raise ValueError("folder_path is not set.")
        # folder_pathを分割する
        folder_names = folder_path.split("/")

        if len(folder_names) <= 1:
            # 現在の実装上、folder_path = ルートフォルダの階層の場合は処理不可
            raise ValueError("folder_path is root folder. Please set folder_path to child folder.")

        # 対象フォルダの上位階層のfolder_idをチェック. folder_idが存在しない場合は処理不可
        parent: Union[ContentFoldersCatalog, None] = None
        for folder_level in range(len(folder_names) - 1):
            if folder_level == 0:
                folder_name = folder_names[folder_level]
            else:
                # 0からfolder_levelまでのフォルダ名を取得する
                folder_name = "/".join(folder_names[:folder_level + 1])

            # folder_nameを取得する
            parent = self.get_content_folder_by_path(folder_name)
            if not parent:
                raise ValueError(f"folder {folder_name} is not exists.")

        # folderの更新処理。parent_idを更新する
        if not parent:
            raise ValueError(f"parent folder {folder.folder_path} is not exists.")
        
        folder.parent_id = parent.id
        
        # folder_type_stringが指定されていない場合は、parentのfolder_type_stringを引き継ぐ
        if not folder.folder_type_string:
            folder.folder_type_string = parent.folder_type_string

        # update_content_folderを呼び出す
        self.update_content_folder(folder)


    def delete_content_folder(self, folder: ContentFoldersCatalog):
        delete_ids = []
        # folder_pathが指定されている場合は、folder_pathからFolderを取得する
        if folder.folder_path:
            folder_path_folder = self.get_content_folder_by_path(folder.folder_path)
            if not folder_path_folder:
                raise ValueError(f"folder {folder.folder_path} is not exists.")
            folder = folder_path_folder
        
        if folder.id:
            # childrenのidを取得する
            children_ids = self.get_content_folder_child_ids(folder.id)
            delete_ids = [folder.id] + children_ids
        else:
            raise ValueError("folder_id is not set.")
        # データベースへ接続
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # delete_idsを削除する
        for delete_id in delete_ids:
            cur.execute("DELETE FROM ContentFoldersCatalog WHERE id=?", (delete_id,))
        conn.commit()
        conn.close()

    # childrenのidを取得する
    def get_content_folder_child_ids(self, folder_id: str) -> list[str]:
        def get_children_recursively(folder_id: str) -> list[str]:
            # データベースへ接続
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id=?", (folder_id,))
                rows = cur.fetchall()

                # データが存在しない場合は空のリストを返す
                if len(rows) == 0:
                    return []

                children = []
                for row in rows:
                    folder_dict = dict(row)
                    children.append(folder_dict["id"])
                    children.extend(get_children_recursively(folder_dict["id"]))
            return children
        
        # フォルダの子供を取得する
        children = get_children_recursively(folder_id)
        return children

    def get_content_folder_ids_by_path(self, folder_path: str) -> list[str]:
        # フォルダのパスを分割する
        folder_names = folder_path.split("/")

        folder_ids = []
        # フォルダ階層毎のfolder_idを取得して、folder_idsに追加する
        # 例： aaa/bbb/ccc の場合、aaaのfolder_idを取得して、aaa/bbbbのfolder_idを取得して、aaa/bbb/cccのfolder_idを取得する
        for folder_level in range(len(folder_names)):
            if folder_level == 0:
                folder_name = folder_names[folder_level]
            else:
                # 0からfolder_levelまでのフォルダ名を取得する
                folder_name = "/".join(folder_names[:folder_level + 1])

            id = self.get_content_folder_by_path(folder_name)
            folder_ids.append(id)

        return folder_ids

    ########################################
    # TagItem関連
    ########################################
    def get_tag_item(self, tag_id: str) -> Union[TagItem, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM TagItems WHERE id=?", (tag_id,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        tag_item_dict = dict(row)
        conn.close()

        return TagItem(**tag_item_dict)
    
    def get_tag_items(self) -> List[TagItem]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM TagItems")
        rows = cur.fetchall()
        tag_items = [TagItem(**dict(row)) for row in rows]
        conn.close()

        return tag_items
    
    def update_tag_item(self, tag_item: TagItem) -> TagItem:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        if self.get_tag_item(tag_item.id) is None:
            cur.execute("INSERT INTO TagItems VALUES (?, ?, ?)", (tag_item.id, tag_item.tag, tag_item.is_pinned))
        else:
            cur.execute("UPDATE TagItems SET tag=?, is_pinned=? WHERE id=?", (tag_item.tag, tag_item.is_pinned, tag_item.id))
        conn.commit()
        conn.close()

        # 更新したTagItemを返す
        return tag_item
    
    def delete_tag_item(self, tag_item: TagItem):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("DELETE FROM TagItems WHERE id=?", (tag_item.id,))
        conn.commit()
        conn.close()

    ########################################
    # VectorDBItem関連
    ########################################
    # Idを指定してVectorDBItemのdictを取得する
    def get_vector_db_item_dict_by_id(self, vector_db_item_id: str) -> Union[dict, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM VectorDBItems WHERE id=?", (vector_db_item_id,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        vector_db_item_dict = dict(row)
        conn.close()

        return vector_db_item_dict

    # Idを指定してVectorDBItemを取得する
    def get_vector_db_by_id(self, vector_db_item_id: str) -> Union[VectorDBItem, None]:
        vector_db_item_dict = self.get_vector_db_item_dict_by_id(vector_db_item_id)
        if vector_db_item_dict is None:
            return None
        return VectorDBItem(**vector_db_item_dict)

    # nameを指定してVectorDBItemのdictを取得する
    def get_vector_db_item_dict_by_name(self, vector_db_item_name: str) -> Union[dict, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM VectorDBItems WHERE name=?", (vector_db_item_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        vector_db_item_dict = dict(row)
        conn.close()

        return vector_db_item_dict

    # Nameを指定してVectorDBItemを取得する
    def get_vector_db_by_name(self, vector_db_item_name: str) -> Union[VectorDBItem, None]:
        vector_db_item_dict = self.get_vector_db_item_dict_by_name(vector_db_item_name)
        if vector_db_item_dict is None:
            return None
        return VectorDBItem(**vector_db_item_dict)
    
    def get_vector_db_items(self) -> List[VectorDBItem]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM VectorDBItems")
        rows = cur.fetchall()
        vector_db_items = [VectorDBItem(**dict(row)) for row in rows]
        conn.close()

        return vector_db_items
    
    # folder_idを指定してパスを取得する
    def get_vector_db_item_path(self, vector_db_item_id: str) -> str:
        vector_db_item = self.get_vector_db_by_id(vector_db_item_id)
        if vector_db_item is None:
            raise ValueError("VectorDBItem not found")
        return vector_db_item.vector_db_url
    
    def update_vector_db_item(self, vector_db_item: VectorDBItem) -> VectorDBItem:
        if not vector_db_item.vector_db_type:
            raise ValueError("vector_db_type must be 1:Chroma or 2:PGVector")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_vector_db_by_id(vector_db_item.id) is None:
            cur.execute("INSERT INTO VectorDBItems VALUES (?, ? , ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (vector_db_item.id, vector_db_item.name, vector_db_item.description, 
                          vector_db_item.vector_db_url, vector_db_item.is_use_multi_vector_retriever, 
                          vector_db_item.doc_store_url, vector_db_item.vector_db_type, 
                          vector_db_item.collection_name, 
                          vector_db_item.chunk_size, vector_db_item.default_search_result_limit, 
                          vector_db_item.default_score_threshold,
                          vector_db_item.is_enabled, vector_db_item.is_system)
                          )
        else:
            cur.execute("UPDATE VectorDBItems SET name=?, description=?, vector_db_url=?, is_use_multi_vector_retriever=?, doc_store_url=?, vector_db_type=?, collection_name=?, chunk_size=?, default_search_result_limit=?, default_score_threshold=?, is_enabled=?, is_system=? WHERE id=?",
                         (vector_db_item.name, vector_db_item.description, vector_db_item.vector_db_url, 
                          vector_db_item.is_use_multi_vector_retriever, vector_db_item.doc_store_url, 
                          vector_db_item.vector_db_type, vector_db_item.collection_name, 
                          vector_db_item.chunk_size, 
                          vector_db_item.default_search_result_limit, 
                          vector_db_item.default_score_threshold,                          
                          vector_db_item.is_enabled, 
                          vector_db_item.is_system, vector_db_item.id)
                          )
        conn.commit()
        conn.close()

        # 更新したVectorDBItemを返す
        return vector_db_item

    def delete_vector_db_item(self, vector_db_item: VectorDBItem):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM VectorDBItems WHERE Id=?", (vector_db_item.id,))
        conn.commit()
        conn.close()

    #################################################
        # Autogen関連
    #################################################
    def get_autogen_llm_config_list(self) -> List[AutogentLLMConfig]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_llm_configs")
        rows = cur.fetchall()
        llm_configs = [AutogentLLMConfig(**dict(row)) for row in rows]
        conn.close()

        return llm_configs
    
    def get_autogen_llm_config(self, llm_config_name: str) -> Union[AutogentLLMConfig, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_llm_configs WHERE name=?", (llm_config_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        llm_config_dict = dict(row)
        conn.close()

        return AutogentLLMConfig(**llm_config_dict)
    
    def update_autogen_llm_config(self, llm_config: AutogentLLMConfig):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_autogen_llm_config(llm_config.name) is None:
            cur.execute("INSERT INTO autogen_llm_configs VALUES (?, ?, ?, ?, ?, ?)", (llm_config.name, llm_config.api_type, llm_config.api_version, llm_config.model, llm_config.api_key, llm_config.base_url))
        else:
            cur.execute("UPDATE autogen_llm_configs SET api_type=?, api_version=?, model=?, api_key=?, base_url=? WHERE name=?", (llm_config.api_type, llm_config.api_version, llm_config.model, llm_config.api_key, llm_config.base_url, llm_config.name))
        conn.commit()
        conn.close()

    def delete_autogen_llm_config(self, llm_config: AutogentLLMConfig):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_llm_configs WHERE name=?", (llm_config.name,))
        conn.commit()
        conn.close()

    def get_autogen_tool(self, tool_name: str) -> Union[AutogenTools, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_tools WHERE name=?", (tool_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        tool_dict = dict(row)
        conn.close()

        return AutogenTools(**tool_dict)
    
    def get_autogen_tool_list(self) -> List[AutogenTools]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_tools")
        rows = cur.fetchall()
        tools = [AutogenTools(**dict(row)) for row in rows]
        conn.close()

        return tools

    def update_autogen_tool(self, tool: AutogenTools):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_autogen_tool(tool.name) is None:
            cur.execute("INSERT INTO autogen_tools VALUES (?, ?, ?)", (tool.name, tool.path, tool.description))
        else:
            cur.execute("UPDATE autogen_tools SET path=?, description=? WHERE name=?", (tool.path, tool.description, tool.name))
        conn.commit()
        conn.close()

    def delete_autogen_tool(self, tool: AutogenTools):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_tools WHERE name=?", (tool.name,))
        conn.commit()
        conn.close()

    #################################################
    # AutogenAgent関連
    #################################################
    def get_autogen_agent_list(self) -> List[AutogenAgent]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_agents")
        rows = cur.fetchall()
        agents = [AutogenAgent(**dict(row)) for row in rows]
        conn.close()

        return agents

    def get_autogen_agent(self, agent_name: str) -> Union[AutogenAgent, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_agents WHERE name=?", (agent_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None
        agent_dict = dict(row)
        conn.close()

        return AutogenAgent(**agent_dict)
    
    def update_autogen_agent(self, agent: AutogenAgent):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_autogen_agent(agent.name) is None:
            cur.execute("INSERT INTO autogen_agents VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (agent.name, agent.description, agent.system_message, 
                         agent.code_execution, agent.llm_config_name, 
                         json.dumps(agent.tool_names, ensure_ascii=False), 
                         json.dumps(agent.vector_db_items,ensure_ascii=False)))
        else:
            cur.execute("UPDATE autogen_agents SET description=?, system_message=?, code_execution=?, llm_config_name=?, tool_names_json=?, vector_db_items_json=? WHERE name=?", 
                        (agent.description, agent.system_message, 
                         agent.code_execution, agent.llm_config_name, 
                         json.dumps(agent.tool_names, ensure_ascii=False), 
                         json.dumps(agent.vector_db_items,ensure_ascii=False), 
                         agent.name))
        conn.commit()
        conn.close()
    
    def delete_autogen_agent(self, agent: AutogenAgent):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_agents WHERE name=?", (agent.name,))
        conn.commit()
        conn.close()
    #################################################
    # AutogenGroupChat関連
    #################################################
    def get_autogen_group_chat_list(self) -> List[AutogenGroupChat]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_group_chats")
        rows = cur.fetchall()
        group_chats = [AutogenGroupChat(**dict(row)) for row in rows]
        conn.close()

        return group_chats  

    def get_autogen_group_chat(self, group_chat_name: str) -> Union[AutogenGroupChat, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_group_chats WHERE name=?", (group_chat_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        group_chat_dict = dict(row)
        conn.close()

        return AutogenGroupChat(**group_chat_dict)
    
    def update_autogen_group_chat(self, group_chat: AutogenGroupChat):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_autogen_group_chat(group_chat.name) is None:
            cur.execute("INSERT INTO autogen_group_chats VALUES (?, ?, ?, ?)", 
                        (group_chat.name, group_chat.description, group_chat.llm_config_name, 
                         json.dumps(group_chat.agent_names, ensure_ascii=False)))
        else:
            cur.execute("UPDATE autogen_group_chats SET description=?, llm_config_name=?, agent_names_json=? WHERE name=?", 
                        (group_chat.description, group_chat.llm_config_name, 
                         json.dumps(group_chat.agent_names, ensure_ascii=False), group_chat.name))
        conn.commit()
        conn.close()

    def delete_autogen_group_chat(self, group_chat: AutogenGroupChat):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_group_chats WHERE name=?", (group_chat.name,))
        conn.commit()
        conn.close()