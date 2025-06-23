import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
import uuid
from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Union

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.vector_db_item import MainDB


class ContentItem(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "ContentItems" (
        "id" TEXT NOT NULL CONSTRAINT "PK_ContentItems" PRIMARY KEY,
        "folder_id" TEXT NULL,
        "created_at" TEXT NOT NULL,
        "updated_at" TEXT NOT NULL,
        "vectorized_at" TEXT NOT NULL,
        "content" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "content_type" INTEGER NOT NULL,
        "chat_messages_json" TEXT NOT NULL,
        "prompt_chat_result_json" TEXT NOT NULL,
        "tag_string" TEXT NOT NULL,
        "is_pinned" INTEGER NOT NULL,
        "cached_base64_string" TEXT NOT NULL,
        "extended_properties_json" TEXT NOT NULL
    )
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the auto process item")
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

    content_item_requests_name: ClassVar[str] = "content_item_requests"
    @classmethod
    async def create_table(cls):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "ContentItems" (
                    "id" TEXT NOT NULL CONSTRAINT "PK_ContentItems" PRIMARY KEY,
                    "folder_id" TEXT NULL,
                    "created_at" TEXT NOT NULL,
                    "updated_at" TEXT NOT NULL,
                    "vectorized_at" TEXT NOT NULL,
                    "content" TEXT NOT NULL,
                    "description" TEXT NOT NULL,
                    "content_type" INTEGER NOT NULL,
                    "chat_messages_json" TEXT NOT NULL,
                    "prompt_chat_result_json" TEXT NOT NULL,
                    "tag_string" TEXT NOT NULL,
                    "is_pinned" INTEGER NOT NULL,
                    "cached_base64_string" TEXT NOT NULL,
                    "extended_properties_json" TEXT NOT NULL
                )
            ''')
            await conn.commit()

    @classmethod
    async def update_default_data(cls):
        # folder_idにインデックスを追加
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_folder_id ON ContentItems (folder_id)
            ''')
            await conn.commit()

    @classmethod
    def get_content_item_request_objects(cls, request_dict: dict) -> List["ContentItem"]:
        '''
        {"content_item_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[List[dict], None] = request_dict.get(cls.content_item_requests_name, None)
        if not request:
            logger.info("content item request is not set. skipping.")
            return []
        
        content_items = []
        for item in request:
            content_item = cls(**item)
            content_items.append(content_item)
        
        return content_items

    @classmethod
    async def get_content_items_by_folder_id(cls, folder_id: str) -> List["ContentItem"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems WHERE folder_id = ?", (folder_id,))
                rows = await cur.fetchall()
                content_items = [ContentItem(**dict(row)) for row in rows]
                return content_items    

    @classmethod
    async def get_content_items(cls) -> List["ContentItem"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems")
                rows = await cur.fetchall()
                content_items = [ContentItem(**dict(row)) for row in rows]
                return content_items

    @classmethod
    async def get_content_item_by_id(cls, item_id: str) -> Optional["ContentItem"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems WHERE id = ?", (item_id,))
                row = await cur.fetchone()
                if row:
                    return ContentItem(**dict(row))
                return None
    
    @classmethod
    async def update_content_item(cls, item: "ContentItem") -> "ContentItem":
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                if await cls.get_content_item_by_id(item.id) is None:
                    # 新規追加
                    await cur.execute('''
                        INSERT INTO ContentItems (
                            id, folder_id, created_at, updated_at, vectorized_at,
                            content, description, content_type, chat_messages_json,
                            prompt_chat_result_json, tag_string, is_pinned,
                            cached_base64_string, extended_properties_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.id, item.folder_id, item.created_at, item.updated_at,
                        item.vectorized_at, item.content, item.description,
                        item.content_type, item.chat_messages_json,
                        item.prompt_chat_result_json, item.tag_string,
                        item.is_pinned, item.cached_base64_string,
                        item.extended_properties_json
                    ))
                else:
                    # 更新
                    await cur.execute('''
                        UPDATE ContentItems SET
                            folder_id = ?, updated_at = ?, vectorized_at = ?,
                            content = ?, description = ?, content_type = ?,
                            chat_messages_json = ?, prompt_chat_result_json = ?,
                            tag_string = ?, is_pinned = ?,
                            cached_base64_string = ?, extended_properties_json = ?
                        WHERE id = ?
                    ''', (
                        item.folder_id, item.updated_at, item.vectorized_at,
                        item.content, item.description, item.content_type,
                        item.chat_messages_json, item.prompt_chat_result_json,
                        item.tag_string, item.is_pinned,
                        item.cached_base64_string, item.extended_properties_json,
                        item.id
                    ))
                await conn.commit()
        return item

    @classmethod
    async def delete_content_item(cls, item: "ContentItem") -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM ContentItems WHERE id = ?", (item.id,))
                await conn.commit()
        logger.info(f"ContentItem with id {item.id} deleted.")

    @classmethod
    async def delete_content_items_by_folder_id(cls, folder_id: str) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM ContentItems WHERE folder_id = ?", (folder_id,))
                await conn.commit()
        logger.info(f"ContentItems in folder {folder_id} deleted.")

    def to_dict(self) -> dict:
        return self.model_dump()
    
    @classmethod
    async def get_content_items_api(cls) -> dict:
        content_items = await cls.get_content_items()
        return {"content_items": [item.to_dict() for item in content_items]}
        
    @classmethod
    async def get_content_item_by_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(cls.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        item_id: str = content_item_requests[0].get("id", "")
        if not item_id:
            raise ValueError("id is not set in the request.")
        
        content_item = await cls.get_content_item_by_id(item_id)
        if not content_item:
            raise ValueError(f"ContentItem with id {item_id} not found.")
        return {"content_item": content_item.to_dict()}
    
    @classmethod
    async def get_content_items_by_folder_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(cls.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        folder_id: str = content_item_requests[0].get("folder_id", "")
        if not folder_id:
            raise ValueError("folder_id is not set in the request.")
        
        content_items = await cls.get_content_items_by_folder_id(folder_id)
        return {"content_items": [item.to_dict() for item in content_items]}
    
    @classmethod
    async def update_content_item_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(cls.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        
        content_items = cls.get_content_item_request_objects(request_dict)
        if not content_items:
            raise ValueError("No valid content items found in the request.")
        
        updated_items = []
        for item in content_items:
            updated_item = await cls.update_content_item(item)
            updated_items.append(updated_item.to_dict())
    
    @classmethod
    async def delete_content_item_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_item_requests: List[dict] = request_dict.get(cls.content_item_requests_name, [])
        if not content_item_requests:
            raise ValueError("content_item_requests is not set in the request.")
        
        item_id: str = content_item_requests[0].get("id", "")
        if not item_id:
            raise ValueError("id is not set in the request.")
        
        content_item = await cls.get_content_item_by_id(item_id)
        if not content_item:
            raise ValueError(f"ContentItem with id {item_id} not found.")
        
        await cls.delete_content_item(content_item)
