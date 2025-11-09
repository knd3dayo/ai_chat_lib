import json
from typing import Optional, ClassVar, List, Union
from vector_search_mcp.model.models import EmbeddingData, VectorSearchRequest

from ai_chat_mcp.chat.chat_util import ChatRequestContext
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.content_item import ContentItem
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.search_rule import SearchRule
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AIAppVectorSearchRequest(VectorSearchRequest):

    async def validate_filter(self):
        if not isinstance(self.filter, dict):
            raise ValueError("filter must be a dictionary.")

        # folder_path が存在するかチェック
        if "folder_path" not in self.filter:
            logger.info("folder_path is not set.")
            return

        folder_path = self.filter["folder_path"]
        folder = await ContentFolder.get_content_folder_by_path(folder_path)
        if not folder:
            logger.info(f"folder_path '{folder_path}' does not exist.")
            return

        # filterのfolder_pathをfolder_idに置換
        self.filter["folder_id"] = folder.id
        del self.filter["folder_path"]


class AIApppEmbeddingData(EmbeddingData):

    
    async def validate_metadata(self):
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary.")
        # folder_path が存在するかチェック
        if "folder_path" not in self.metadata:
            raise ValueError("metadata must contain 'folder_path'.")
        # source_type が存在するかチェック
        if "source_type" not in self.metadata:
            raise ValueError("metadata must contain 'source_type'.")
        # description が存在するかチェック
        if "description" not in self.metadata:
            raise ValueError("metadata must contain 'description'.")

        # source_path が存在するかチェック
        if "source_path" not in self.metadata:
            raise ValueError("metadata must contain 'source_path'.")
        # image_url が存在するかチェック
        if "image_url" not in self.metadata:
            raise ValueError("metadata must contain 'image_url'.")

        # folder_pathからfolder_idを取得してmetadataに追加
        folder_path = self.metadata.get("folder_path", "")
        folder = await ContentFolder.get_content_folder_by_path(folder_path)
        if not folder:
            raise ValueError(f"folder_path '{folder_path}' does not exist.")
        self.metadata["folder_id"] = folder.id if folder else ""

        # folder_pathを削除
        del self.metadata["folder_path"]

class AIAppData:

    chat_request_context_name: ClassVar[str] = "chat_request_context"

    @classmethod
    def get_chat_request_context_objects(cls, request_dict: dict) -> ChatRequestContext:
        '''
        {"chat_request_context": {}}の形式で渡される
        '''
        chat_request_context_dict = request_dict.get(cls.chat_request_context_name, None)
        if not chat_request_context_dict:
            raise ValueError("request_context is not set.")
        return ChatRequestContext(**chat_request_context_dict)

    embedding_request_name: ClassVar[str] = "embedding_request"

    @classmethod
    async def get_embedding_request_objects(cls, request_dict: dict) -> AIApppEmbeddingData:
        '''
        {"embedding_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.embedding_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        embedding_data = AIApppEmbeddingData(**request)
        await embedding_data.validate_metadata()
        return embedding_data

    vector_search_request_name: ClassVar[str] = "vector_search_request"

    @classmethod
    async def get_vector_search_request_objects(cls, request_dict: dict) -> AIAppVectorSearchRequest:
        '''
        {"vector_search_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[dict, None] = request_dict.get(cls.vector_search_request_name, None)
        if not request:
            raise ValueError("vector_search_request is not set.")

        vector_search_request = AIAppVectorSearchRequest(**request)
        await vector_search_request.validate_filter()

        return vector_search_request


    file_request_name = "file_request"
    @classmethod
    def get_file_request_objects(cls, request_dict: dict) -> dict:
        '''
        {"context": {"file_request": {}}}の形式で渡される
        '''
        # contextを取得
        request = request_dict.get(cls.file_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return request

    excel_request_name = "excel_request"
    @classmethod
    def get_excel_request_objects(cls, request_dict: dict) -> tuple[str, dict]:
        '''
        {"context": {"excel_request": {}}}の形式で渡される
        '''
        # contextを取得
        request:Union[dict, None] = request_dict.get(cls.excel_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        # file_pathとdata_jsonを取得
        file_path = request.get("file_path", None)
        data_json = request.get("data_json", "[]")
        data = json.loads(data_json)

        return file_path, data


    web_request_name = "web_request"
    @classmethod
    def get_web_request_objects(cls, request_dict: dict) -> dict:
        '''
        {"context": {"web_request": {}}}の形式で渡される
        '''
        # contextを取得
        from typing import Optional
        request: Optional[dict] = request_dict.get(cls.web_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return request


    auto_process_item_requests_name: ClassVar[str] = "auto_process_item_requests"

    @classmethod
    async def get_auto_process_item_objects(cls, request_dict: dict) -> list:
        '''
        {"auto_process_item_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[list[dict], None] = request_dict.get(cls.auto_process_item_requests_name, None)
        if not request:
            logger.info("auto process item request is not set. skipping.")
            return []
        auto_process_items = []
        for item in request:
            auto_process_item = cls(**item)
            auto_process_items.append(auto_process_item)
        return auto_process_items
    

    auto_process_rule_requests_name: ClassVar[str] = "auto_process_rule_requests"
    @classmethod
    async def get_auto_process_rule_objects(cls, request_dict: dict) -> list:
        '''
        {"auto_process_rule_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[list[dict], None] = request_dict.get(cls.auto_process_rule_requests_name, None)
        if not request:
            logger.info("auto process rule request is not set. skipping.")
            return []
        auto_process_rules = []
        for item in request:
            auto_process_rule = cls(**item)
            auto_process_rules.append(auto_process_rule)
        return auto_process_rules


    get_content_folder_requests_name: ClassVar[str] = "content_folder_requests"

    @classmethod
    def get_content_folder_request_objects(cls, request_dict: dict) -> List["ContentFolder"]:
        '''
        {"content_folder_requests": [] }の形式で渡される
        '''
        content_folders = request_dict.get(cls.get_content_folder_requests_name, None)
        if not content_folders:
            raise ValueError("content_folder is not set.")
        return [ContentFolder(**item) for item in content_folders]


    content_item_requests_name: ClassVar[str] = "content_item_requests"

    @classmethod
    def get_content_item_request_objects(cls, request_dict: dict) -> List["ContentItem"]:
        """
        APIリクエストdictからContentItemオブジェクトリストを生成する。

        Args:
            request_dict (dict): {"content_item_requests": [{...}, ...]} 形式のリクエスト

        Returns:
            List[ContentItem]: ContentItemインスタンスのリスト
        """
        request: Union[List[dict], None] = request_dict.get(cls.content_item_requests_name, None)
        if not request:
            logger.info("content item request is not set. skipping.")
            return []
        
        content_items = []
        for item in request:
            content_item = ContentItem(**item)
            content_items.append(content_item)
        
        return content_items

    
    get_prompt_item_requests_name: ClassVar[str] = "prompt_item_requests"

    
    @classmethod
    def get_prompt_item_objects(cls, request_dict: dict) -> list["PromptItem"]:
        '''
        {"prompt_ttem_requests": [] }の形式で渡される
        '''
        prompt_items = request_dict.get(cls.get_prompt_item_requests_name, None)
        if not prompt_items:
            raise ValueError("prompt_items is not set.")
        return [PromptItem(**item) for item in prompt_items]


    search_rule_requests_name: ClassVar[str] = "search_rule_requests"

    @classmethod
    async def get_search_rule_objects(cls, request_dict: dict) -> list:
        '''
        {"search_rule_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[list[dict], None] = request_dict.get(cls.search_rule_requests_name, None)
        if not request:
            logger.info("search rule request is not set. skipping.")
            return []
        search_rules = []
        for item in request:
            search_rule = SearchRule(**item)
            search_rules.append(search_rule)
        return search_rules


    @classmethod
    async def get_tag_item_objects(cls, request_dict: dict) -> List["TagItem"]:
        '''
        {"tag_item_requests": []}の形式で渡される
        '''
        tag_items: Optional[List[dict]] = request_dict.get("tag_item_requests", None)
        if not tag_items:
            raise ValueError("tag_items is not set.")
        return [TagItem(**item) for item in tag_items]


    vector_db_item_request_name: ClassVar[str] = "vector_db_item_request"

    @classmethod
    def get_vector_db_item_object(cls, request_dict: dict) -> "VectorDBItem":
        vector_db_item_request = request_dict.get(cls.vector_db_item_request_name, None)
        if not vector_db_item_request:
            raise ValueError("vector_db_item_request is not set.")
        return VectorDBItem(**vector_db_item_request)
