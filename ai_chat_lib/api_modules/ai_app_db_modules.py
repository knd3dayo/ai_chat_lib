import json
from typing import ClassVar, List, Union
from ai_chat_lib.db_modules.content_item import ContentItem, SearchCondition
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.auto_process_item import AutoProcessItem
from ai_chat_lib.db_modules.auto_process_rule import AutoProcessRule
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.search_rule import SearchRule
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem

from ai_chat_lib.api_modules.ai_app_data import AIAppData
import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AutoProcessItemAPI:

    @classmethod
    async def get_auto_process_items_api(cls, request_json: str) -> dict:
        items = await AutoProcessItem.get_auto_process_items()
        result: dict = {}
        result["auto_process_items"] = [item.dict() for item in items]
        return result
    
    @classmethod
    async def update_auto_process_items_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        items = await AIAppData.get_auto_process_item_objects(request_dict)
        result: dict = {}
        result["auto_process_items"] = [await AutoProcessItem.update_auto_process_item(item) for item in items]
        return result
    
    @classmethod
    async def delete_auto_process_items_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        items = await AIAppData.get_auto_process_item_objects(request_dict)
        result: dict = {}
        for item in items:
            await AutoProcessItem.delete_auto_process_item(item)
        result["deleted"] = True
        return result
class AutoProcessRuleAPI:

    @classmethod
    async def get_auto_process_rules_api(cls, request_json: str) -> dict:
        rules = await AutoProcessRule.get_auto_process_rules()
        result: dict = {}
        result["auto_process_rules"] = [rule.dict() for rule in rules]
        return result
    
    @classmethod
    async def update_auto_process_rules_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        rules = await AIAppData.get_auto_process_rule_objects(request_dict)
        result: dict = {}
        result["auto_process_rules"] = [await AutoProcessRule.update_auto_process_rule(rule) for rule in rules]
        return result
    
    @classmethod
    async def delete_auto_process_rules_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        rules = await AIAppData.get_auto_process_rule_objects(request_dict)
        result: dict = {}
        for rule in rules:
            await AutoProcessRule.delete_auto_process_rule(rule)
        result["deleted"] = True
        return result
    
class ContentItemAPI:
        
    @classmethod
    async def get_content_item_by_id_api(cls, request_json: str) -> dict:
        """
        指定IDのContentItemをAPIレスポンス形式で取得する。

        Args:
            request_json (str): {"content_item_requests": [{"id": ...}]} 形式のJSON

        Returns:
            dict: {"content_item": {...}}
        """
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(AIAppData.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        item_id: str = content_item_requests[0].get("id", "")
        if not item_id:
            raise ValueError("id is not set in the request.")
        
        content_item = await ContentItem.get_content_item_by_id(item_id)
        if not content_item:
            raise ValueError(f"ContentItem with id {item_id} not found.")
        return {"content_item": content_item.to_dict()}
    
    @classmethod
    async def get_content_items_by_folder_id_api(cls, request_json: str) -> dict:
        """
        指定フォルダID配下のContentItemをAPIレスポンス形式で取得する。

        Args:
            request_json (str): {"content_item_requests": [{"folder_id": ...}]} 形式のJSON

        Returns:
            dict: {"content_items": [ ... ]}
        """
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(AIAppData.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        folder_id: str = content_item_requests[0].get("folder_id", "")
        if not folder_id:
            raise ValueError("folder_id is not set in the request.")

        content_items = await ContentItem.get_content_items_by_folder_id(folder_id)
        return {"content_items": [item.to_dict() for item in content_items]}
    
    @classmethod
    async def update_content_items_api(cls, request_json: str) -> dict:
        """
        ContentItemの追加・更新をAPIリクエスト形式で受け付けて実行する。

        Args:
            request_json (str): {"content_item_requests": [ ... ]} 形式のJSON

        Raises:
            ValueError: リクエスト不備時
        """
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(AIAppData.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")

        content_items = AIAppData.get_content_item_request_objects(request_dict)
        if not content_items:
            raise ValueError("No valid content items found in the request.")
        
        updated_items = []
        for item in content_items:
            updated_item = await ContentItem.update_content_item(item)
            updated_items.append(updated_item.to_dict())
        return {}
        
    @classmethod
    async def delete_content_items_api(cls, request_json: str) -> dict:
        """
        ContentItemの削除をAPIリクエスト形式で受け付けて実行する。

        Args:
            request_json (str): {"content_item_requests": [{"id": ...}]} 形式のJSON

        Raises:
            ValueError: リクエスト不備時や該当ID未存在時
        """
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(AIAppData.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        
        item_id: str = content_item_requests[0].get("id", "")
        if not item_id:
            raise ValueError("id is not set in the request.")

        content_item = await ContentItem.get_content_item_by_id(item_id)
        if not content_item:
            raise ValueError(f"ContentItem with id {item_id} not found.")
        
        await ContentItem.delete_content_item(content_item)
        return {}

    @classmethod
    async def search_content_items_api(cls, request_json: str) -> dict:
        """
        ContentItemの検索をAPIリクエスト形式で受け付けて実行する。

        Args:
            request_json (str): {"search_request": { ... }} 形式のJSON

        Returns:
            dict: {"content_items": [ ... ]}
        """
        request_dict: dict = json.loads(request_json)
        search_condition_data = request_dict.get("search_request", {})
        search_condition = SearchCondition(**search_condition_data)

        content_items = await ContentItem.search_content_items(search_condition)
        return {"content_items": [item.to_dict() for item in content_items]}
    
class ContentFolderAPI:
    
    @classmethod
    async def get_root_content_folders_api(cls) -> dict:
        content_folders = await ContentFolder.get_root_content_folders()
        result = {}
        result["content_folders"] = [item.model_dump() for item in content_folders]
        return result

    @classmethod
    async def get_content_folders_api(cls) -> dict:
        content_folders = await ContentFolder.get_content_folders()
        result = {}
        result["content_folders"] = [item.model_dump() for item in content_folders]
        return result

    @classmethod
    async def get_content_folder_by_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_folder_id = AIAppData.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder = await ContentFolder.get_content_folder_by_id(content_folder_id)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] =  content_folder.model_dump()
        return result

    @classmethod
    async def get_parent_content_folder_by_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_folder_id = AIAppData.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder = await ContentFolder.get_content_folder_by_id(content_folder_id)
        if not content_folder:
            raise ValueError("content_folder is not found")
        parent_content_folder = await ContentFolder.get_parent_content_folder_by_id(content_folder)
        result: dict = {}
        if parent_content_folder is not None:
            result["content_folders"] =  parent_content_folder.model_dump()
        return result
    
    @classmethod
    async def get_child_content_folders_by_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_folder_id = AIAppData.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder = await ContentFolder.get_content_folder_by_id(content_folder_id)
        if not content_folder:
            raise ValueError("content_folder is not found")
        child_content_folders = await ContentFolder.get_child_content_folders_by_id(content_folder)
        result: dict = {}
        result["content_folders"] = [item.model_dump() for item in child_content_folders]
        return result

    @classmethod
    async def update_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = AIAppData.get_content_folder_request_objects(request_dict)
        for content_folder in content_folders:
            await ContentFolder.update_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    async def delete_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = AIAppData.get_content_folder_request_objects(request_dict)
        for content_folder in content_folders:
            await ContentFolder.delete_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    async def get_content_folder_by_path_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_path = request_dict.get("content_folder_path", None)
        if not content_folder_path:
            raise ValueError("content_folder_path is not set")
        content_folder = await ContentFolder.get_content_folder_by_path(content_folder_path)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] =  content_folder.model_dump()
        return result

    @classmethod
    async def get_content_folder_path_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_id = AIAppData.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder_path = await ContentFolder.get_content_folder_path_by_id(content_folder_id)
        result: dict = {}
        if content_folder_path is not None:
            result["content_folder_path"] = content_folder_path
        return result

class PromptItemAPI:

    @classmethod
    async def get_prommt_items_api(cls) -> dict:
        """
        PromptItemsテーブルから全てのデータを取得し、API用の辞書形式で返す
        """
        prompt_items = await PromptItem.get_prompt_items()
        return {
            "prompt_items": [item.model_dump() for item in prompt_items],
        }
    
    @classmethod
    async def get_prompt_item_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを取得し、API用の辞書形式で返す
        """
        request_dict: dict = json.loads(request_json)
        id: Union[str, None] = AIAppData.get_prompt_item_objects(request_dict)[0].id if AIAppData.get_prompt_item_objects(request_dict) else None
        if id is None:
            raise ValueError("id is not set in the request.")
        prompt_item = await PromptItem.get_prompt_item_by_id(id)
        if prompt_item is None:
            return {"prompt_item": None}
        return{
            "prompt_item": prompt_item.model_dump()
        }
    
    @classmethod
    async def update_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルのデータを更新する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = AIAppData.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            prompt_item = PromptItem(**prompt_item_data.model_dump())
            await PromptItem.update_prompt_item(prompt_item)
    
        return {}
    
    @classmethod
    async def delete_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを削除する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = AIAppData.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            await PromptItem.delete_prompt_item(prompt_item_data.id)

        return {}

class SearchRuleAPI:

    @classmethod
    async def get_search_rules_api(cls, request_json: str) -> dict:
        search_rules = await SearchRule.get_search_rules()
        result: dict = {}
        result["search_rules"] = [search_rule.model_dump() for search_rule in search_rules]

        return result

    @classmethod
    async def update_search_rules_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        search_rules = await AIAppData.get_search_rule_objects(request_dict)
        for search_rule in search_rules:
            await SearchRule.update_search_rule(search_rule)
        result: dict = {}
        return result
    @classmethod
    async def delete_search_rules_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        search_rules = await AIAppData.get_search_rule_objects(request_dict)
        for search_rule in search_rules:
            await SearchRule.delete_search_rule(search_rule)
        result: dict = {}
        return result

class TagItemAPI:
    @classmethod
    async def get_tag_items_api(cls, request_json: str):
        tag_items = await TagItem.get_tag_items()
        result: dict = {}
        result["tag_items"] = [item.model_dump() for item in tag_items]
        return result

    @classmethod
    async def update_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = await AIAppData.get_tag_item_objects(request_dict)
        for tag_item in tag_items:
            await TagItem.update_tag_item(tag_item)
        result: dict = {}
        return result

    @classmethod
    async def delete_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = await AIAppData.get_tag_item_objects(request_dict)
        for tag_item in tag_items:
            await TagItem.delete_tag_item(tag_item)
        result: dict = {}
        return result

class VectorDBItemAPI:

    @classmethod
    async def update_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = AIAppData.get_vector_db_item_object(request_dict)
        await VectorDBItem.update_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.model_dump()
        return result

    @classmethod
    async def delete_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = AIAppData.get_vector_db_item_object(request_dict)
        await VectorDBItem.delete_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.model_dump()
        return result

    @classmethod
    async def get_vector_db_items_api(cls):
        vector_db_list = await VectorDBItem.get_vector_db_items()
        result = {}
        result["vector_db_items"] = [item.model_dump() for item in vector_db_list]
        return result

    @classmethod
    async def get_vector_db_item_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_id = AIAppData.get_vector_db_item_object(request_dict).id
        if not vector_db_id:
            raise ValueError("vector_db_id is not set")
        vector_db_item = await VectorDBItem.get_vector_db_by_id(vector_db_id)
        result: dict = {}
        if vector_db_item is not None:
            result["vector_db_item"] = vector_db_item.model_dump()
        return result

    @classmethod
    async def get_vector_db_item_by_name_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_name = AIAppData.get_vector_db_item_object(request_dict).name
        if not vector_db_name:
            raise ValueError("vector_db_name is not set")
        vector_db = await VectorDBItem.get_vector_db_by_name(vector_db_name)
        result: dict = {}
        if vector_db is not None:
            result["vector_db_item"] = vector_db.model_dump()
        return result