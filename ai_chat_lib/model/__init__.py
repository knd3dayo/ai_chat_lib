import uuid
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ModelBase(BaseModel):
    pass

class ContentItemModel(ModelBase):
    """
    ContentItemモデル
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the content item")
    folder_id: str = Field(..., description="ID of the folder this content item belongs to")
    created_at: str = Field(..., description="Creation timestamp of the content item")
    updated_at: str = Field(..., description="Last updated timestamp of the content item")
    vectorized_at: str = Field(..., description="Timestamp when the content was vectorized")
    content: str = Field(..., description="Content of the item, can be text or other data")
    description: str = Field(..., description="Description of the content item")
    content_type: int = Field(..., description="Type of content, e.g., text, image, etc.")
    chat_messages_json: str = Field(..., description="JSON string of chat messages associated with the content item")
    prompt_chat_result_json: str = Field(..., description="JSON string of the result from the prompt chat")
    tag_string: str = Field(..., description="Comma-separated string of tags associated with the content item")
    is_pinned: int = Field(..., description="Flag indicating if the content item is pinned (1 for pinned, 0 for not pinned)")
    cached_base64_string: str = Field(..., description="Base64 encoded string of the cached content")
    extended_properties_json: str = Field(..., description="JSON string of extended properties for the content item")

class ContentFolderModel(ModelBase):
    """
    ContentFolderモデル
    """
    id: Optional[str] = None
    folder_type_string: Optional[str] = None
    parent_id: Optional[str] = None
    folder_name: Optional[str] = None
    description: Optional[str] = None
    extended_properties_json: Optional[str] = None
    folder_path: Optional[str] = None
    is_root_folder: bool = False

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

class AutoProcessItemModel(ModelBase):
    '''
    自動処理アイテムモデル
    - 自動処理アイテムタイプ
      - 0:SystemDefined
      - 1:UserDefined
    - アクションタイプ
      - 0:Ignore
      - 1:CopyToFolder
      - 2:MoveToFolder
      - 3:ExtractText
      - 4:PromptTemplate
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the auto process item")
    display_name: str = Field(..., description="Display name of the auto process item")
    description: str = Field(..., description="Description of the auto process item")
    auto_process_item_type: int = Field(default=1, description="Type of the auto process item, 0 for SystemDefined, 1 for UserDefined")
    action_type: int = Field(..., description="Type of action associated with the auto process item")

class AutoProcessRuleModel(ModelBase):
    '''
    自動処理ルールモデル
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the auto process rule")
    rule_name : str = Field(..., description="Name of the auto process rule")
    is_enabled: bool = Field(default=True, description="Whether the rule is enabled or not")
    priority: int = Field(default=0, description="Priority of the rule, lower numbers indicate higher priority")
    conditions_json: str = Field(..., description="JSON string representing the conditions for the rule")
    auto_process_item_id: Optional[str] = Field(None, description="ID of the auto process item associated with the rule")
    target_folder_id: Optional[str] = Field(None, description="ID of the target folder for the rule")
    destination_folder_id: Optional[str] = Field(None, description="ID of the destination folder for the rule")

class SearchRuleModel(ModelBase):
    '''
    検索ルールモデル
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the search rule")
    name: str = Field(..., description="Name of the search rule")
    search_condition_json: str = Field(..., description="JSON string representing the search conditions")
    is_include_sub_folder: bool = Field(default=False, description="Whether to include subfolders in the search")
    is_global_search: bool = Field(default=False, description="Whether the search is a global search")
    search_folder_id: Optional[str] = Field(None, description="ID of the folder to search in")
    target_folder_id: Optional[str] = Field(None, description="ID of the target folder for the search results")

class PromptItemModel(ModelBase):
    '''
    プロンプトアイテムモデル
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the prompt item")
    name: str = Field(..., description="Name of the prompt item")
    description: str = Field(..., description="Description of the prompt item")
    prompt: str = Field(..., description="The prompt text")
    prompt_template_type: int = Field(..., description="Type of the prompt template")
    extended_properties_json: str = Field(..., description="JSON string of extended properties")

class TagItemModel(ModelBase):
    '''
    タグアイテムモデル
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

