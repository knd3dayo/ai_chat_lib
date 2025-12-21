import uuid
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime, timezone

# vector search util
import vector_search_util.api.api_server as vector_db_api
import vector_search_util.model as vector_model

class ModelBase(BaseModel):
    pass

class ContentItemModel(ModelBase):
    """
    ContentItemモデル
    """
    source_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the content item")
    category: str = Field(..., description="ID of the folder this content item belongs to")
    updated_at: datetime = Field(..., description="Last updated timestamp of the content item")
    source_content: str = Field(..., description="Content of the item, can be text or other data")

    created_at: datetime = Field(..., description="Creation timestamp of the content item")
    title: str = Field(..., description="Description of the content item")
    content_type: int = Field(..., description="Type of content, e.g., text, image, etc.")
    tags: str = Field(..., description="Comma-separated string of tags associated with the content item")
    is_pinned: int = Field(..., description="Flag indicating if the content item is pinned (1 for pinned, 0 for not pinned)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the content item")

    @classmethod
    def to_source_document(cls, item: "ContentItemModel") -> vector_model.SourceDocumentData:
        """
        Convert ContentItemModel to source document dictionary
        """
        source_document_metadata = {
            "created_at": item.created_at,
            "title": item.title,
            "content_type": item.content_type,
            "tags": item.tags,
            "is_pinned": item.is_pinned,
            **item.metadata
        }

        source_document = vector_model.SourceDocumentData(
            source_id=item.source_id,
            source_content=item.source_content,
            category=item.category,
            updated_at=item.updated_at,
            metadata=source_document_metadata
        )
        return source_document

    @classmethod
    def from_source_document(cls, doc: vector_model.SourceDocumentData) -> "ContentItemModel":
        """
        Create ContentItemModel from source document dictionary
        """
        metadata = doc.metadata.copy()
        created_at = metadata.pop("created_at", datetime.now(timezone.utc))
        title = metadata.pop("title", "")
        content_type = metadata.pop("content_type", 0)
        tags = metadata.pop("tags", "")
        is_pinned = metadata.pop("is_pinned", 0)

        content_item = ContentItemModel(
            source_id=doc.source_id,
            source_content=doc.source_content,
            category=doc.category,
            updated_at=doc.updated_at,
            created_at=created_at,
            title=title,
            content_type=content_type,
            tags=tags,
            is_pinned=is_pinned,
            metadata=metadata
        )
        return content_item

    @classmethod
    async def get_items(cls) -> list["ContentItemModel"]:
        documents = await vector_db_api.get_documents()
        content_items = [ContentItemModel.from_source_document(doc) for doc in documents]
        return content_items

    @classmethod
    async def get_items_by_category_id(cls, category_id: str) -> list["ContentItemModel"]:
        condition = vector_model.EqCondition(
                    field="category",
                    value=category_id
                    )
        condtion_container = vector_model.ConditionContainer(
            conditions=[condition]
        )
        documents = await vector_db_api.get_documents(conditions=condtion_container)
        content_items = [ContentItemModel.from_source_document(doc) for doc in documents]
        return content_items

    @classmethod
    async def get_item_by_id(cls, item_id: str) -> "ContentItemModel | None":
        documents = await vector_db_api.get_documents(source_ids=[item_id])
        if len(documents) == 0:
            return None
        content_item = ContentItemModel.from_source_document(documents[0])
        return content_item

    @classmethod
    async def update_content_items(cls, content_items: list["ContentItemModel"]):
        documents = [ContentItemModel.to_source_document(item) for item in content_items]
        await vector_db_api.upsert_documents(documents)

    @classmethod
    async def delete_content_items(cls, items: list["ContentItemModel"]) -> None:
        source_id_list = [item.source_id for item in items]
        await vector_db_api.delete_documents(source_id_list)


class ContentFolderModel(ModelBase):
    """
    ContentFolderモデル
    """
    name: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the content folder")
    description: str = Field(default="", description="Description of the folder")

    parent: str = Field(default="", description="ID of the parent folder, empty if root folder")

    folder_type: str = Field(..., description="Type of the folder")
    parent_id: Optional[str] = Field(None, description="ID of the parent folder, None if root folder")
    is_root_folder: bool = Field(False, description="Flag indicating if the folder is a root folder")

    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the content item")


    @classmethod
    def to_category_data(cls, folder: "ContentFolderModel") -> tuple[vector_model.CategoryData, vector_model.RelationData | None]:
        """
        Convert ContentFolderModel to category data dictionary
        """
        category_metadata = {
            "folder_type": folder.folder_type,
            "description": folder.description,
            "is_root_folder": folder.is_root_folder,
            **folder.metadata
        }

        category_data = vector_model.CategoryData(
            name=folder.name,
            description=folder.description,
            metadata=category_metadata
        )
        relation_data = None
        if folder.parent_id is not None:
            relation_data = vector_model.RelationData(
                from_node=folder.name,
                to_node=folder.parent_id,
                edge_type="parent_child"
            )
        return category_data, relation_data
    
    @classmethod
    def from_category_data(
        cls, category: vector_model.CategoryData, 
        relation: Optional[vector_model.RelationData] = None) -> "ContentFolderModel":
        """
        Create ContentFolderModel from category data dictionary
        """
        metadata = category.metadata.copy()
        folder_type = metadata.pop("folder_type", "")
        description = metadata.pop("description", "")
        is_root_folder = metadata.pop("is_root_folder", False)

        parent_id = relation.to_node if relation is not None and relation.edge_type == "parent_child" else None

        content_folder = ContentFolderModel(
            name=category.name,
            description=description,
            folder_type=folder_type,
            is_root_folder=is_root_folder,
            parent_id=parent_id,
            metadata=metadata
        )
        return content_folder

    @classmethod
    def to_relation_data(cls, folder: "ContentFolderModel") -> vector_model.RelationData:
        """
        Convert ContentFolderModel to relation data dictionary
        """
        relation_data = vector_model.RelationData(
            from_node=folder.name,
            to_node=folder.parent,
            edge_type="parent_child"
        )
        return relation_data
    
    @classmethod
    def from_relation_data(cls, relation: vector_model.RelationData, folder: "ContentFolderModel") -> "ContentFolderModel":
        """
        Create ContentFolderModel from relation data dictionary
        """
        if relation.edge_type != "parent_child":
            raise ValueError("Invalid edge_type for ContentFolderModel")
        
        folder.parent = relation.to_node
        return folder

    @classmethod
    async def get_root_folders(cls) -> list["ContentFolderModel"]:
        """
        Get root folders
        """
        condition = vector_model.EqCondition(
                    field="is_root_folder",
                    value=True
                    )
        condtion_container = vector_model.ConditionContainer(
            conditions=[condition]
        )
        categories = await vector_db_api.get_categories(name_list=[], conditions=condtion_container)
        content_folders = [ContentFolderModel.from_category_data(cat) for cat in categories]
        return content_folders

    @classmethod
    async def get_folder_by_id(cls, folder_id: str) -> "ContentFolderModel | None":
        categories = await vector_db_api.get_categories(name_list=[folder_id])
        if len(categories) == 0:
            return None
        content_folder = ContentFolderModel.from_category_data(categories[0])
        return content_folder

    @classmethod
    async def get_folder_by_path(cls, folder_path: str) -> "ContentFolderModel | None":
        categories = await vector_db_api.get_categories(name_list=[folder_path])
        if len(categories) == 0:
            return None
        content_folder = ContentFolderModel.from_category_data(categories[0])
        return content_folder

    @classmethod
    async def get_folder_path_by_id(cls, folder_id: str) -> str | None:
        categories = await vector_db_api.get_categories(name_list=[folder_id])
        if len(categories) == 0:
            return None
        return categories[0].name

    @classmethod
    async def get_parent_folder_by_id(cls, folder_id: str) -> "ContentFolderModel | None":

        relations = await vector_db_api.get_relations(
            to_nodes=[folder_id],
            edge_types=["parent_child"]
        )
        if len(relations) == 0:
            return None
        parent_folder_id = relations[0].from_node
        parent_categories = await vector_db_api.get_categories(name_list=[parent_folder_id])
        if len(parent_categories) == 0:
            return None
        parent_content_folder = ContentFolderModel.from_category_data(parent_categories[0])
        return parent_content_folder

    @classmethod
    async def get_child_folders_by_id(cls, folder_id: str) -> list["ContentFolderModel"]:
        relations = await vector_db_api.get_relations(
            from_nodes=[folder_id],
            edge_types=["parent_child"]
        )
        child_folder_ids = [rel.to_node for rel in relations]
        if len(child_folder_ids) == 0:
            return []
        child_categories = await vector_db_api.get_categories(name_list=child_folder_ids)
        child_content_folders = [ContentFolderModel.from_category_data(cat) for cat in child_categories]
        return child_content_folders

    @classmethod
    async def update_folders(cls, folders: list["ContentFolderModel"]):
        categories = []
        for folder in folders:
            category = ContentFolderModel.to_category_data(folder)
            categories.append(category)
        response = await vector_db_api.upsert_categories(categories)


    @classmethod
    async def delete_folders(cls, folders: list["ContentFolderModel"]):
        categories = []
        for folder in folders:
            category = ContentFolderModel.to_category_data(folder)
            categories.append(category)

        response = await vector_db_api.delete_categories(categories)

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

