import json
from typing import Optional, ClassVar, List, Union
from ai_chat_lib.chat_modules.langchain.embedding_data import EmbeddingData
from ai_chat_lib.chat_modules.util.chat_util import ChatRequestContext
from ai_chat_lib.chat_modules.langchain.vector_search_request import VectorSearchRequest
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.content_item import ContentItem
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.search_rule import SearchRule
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AIAppData:

    embedding_request_name: ClassVar[str] = "embedding_request"

    @classmethod
    def get_embedding_request_objects(cls, request_dict: dict) -> EmbeddingData:
        '''
        {"embedding_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.embedding_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return EmbeddingData(**request)

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


    vector_search_requests_name: ClassVar[str] = "vector_search_requests"

    @classmethod
    async def get_vector_search_requests_objects(cls, request_dict: dict) -> List["VectorSearchRequest"]:
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
            vector_search_request.search_kwargs = await vector_search_request.__update_search_kwargs(vector_search_request.search_kwargs)
            vector_search_requests.append(vector_search_request)
        return vector_search_requests    


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
