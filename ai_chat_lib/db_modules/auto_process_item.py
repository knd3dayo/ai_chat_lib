from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
import json
import uuid
from ai_chat_lib.resouces import *
from ai_chat_lib.db_modules.main_db import MainDB

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AutoProcessItem(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "AutoProcessItems" (
        "id" TEXT NOT NULL CONSTRAINT "PK_AutoProcessItems" PRIMARY KEY,
        "display_name" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "auto_process_item_type" INTEGER NOT NULL,
        "action_type" INTEGER NOT NULL,
    )
    auto_process_item_typeの値は以下のように定義される
    - 0: SystemDefined
    - 1: UserDefined,

    action_typeの値は以下のように定義される
    - 0:Ignore,
    - 1:CopyToFolder,
    - 2:MoveToFolder,
    - 3:ExtractText,
    - 4:PromptTemplate
 
    '''
    id: str = Field(..., description="Unique identifier for the auto process item")
    display_name: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Display name of the auto process item")
    description: str = Field(..., description="Description of the auto process item")
    auto_process_item_type: int = Field(default=1, description="Type of the auto process item, 0 for SystemDefined, 1 for UserDefined")
    action_type: int = Field(..., description="Type of action associated with the auto process item")

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
    

    @classmethod
    async def create_table(cls) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "AutoProcessItems" (
                    "id" TEXT NOT NULL CONSTRAINT "PK_AutoProcessItems" PRIMARY KEY,
                    "display_name" TEXT NOT NULL,
                    "description" TEXT NOT NULL,
                    "auto_process_item_type" INTEGER NOT NULL,
                    "action_type" INTEGER NOT NULL
                )
            ''')
            await conn.commit()

        await cls.update_default_data()

    @classmethod
    async def update_default_data(cls) -> None:
        resources = resource_util.get_string_resources()

        # デフォルトの自動処理アイテムを初期化する
        # Ignore
        ignore_item = await cls.get_auto_process_item("ignore")
        if ignore_item is None:
            ignore_item_id  = "ignore"
        else:
            ignore_item_id = str(uuid.uuid4())
    
        ignore_item = cls(
            id=ignore_item_id,
            display_name=resources.auto_process_item_name_ignore,
            description=resources.auto_process_item_description_ignore,
            action_type=0  # 0はデフォルトのアクションタイプ
        )
        # CopyToFolder
        copy_to_folder_item = await cls.get_auto_process_item("copy_to_folder")
        if copy_to_folder_item is None:
            copy_to_folder_item_id = "copy_to_folder"
        else:
            copy_to_folder_item_id = str(uuid.uuid4())
        copy_to_folder_item = cls(
            id=copy_to_folder_item_id,
            display_name=resources.auto_process_item_name_copy_to_folder,
            description=resources.auto_process_item_description_copy_to_folder,
            action_type=1  # 1はCopyToFolderのアクションタイプ
        )
        # MoveToFolder
        move_to_folder_item = await cls.get_auto_process_item("move_to_folder")
        if move_to_folder_item is None:
            move_to_folder_item_id = "move_to_folder"
        else:
            move_to_folder_item_id = str(uuid.uuid4())
        move_to_folder_item = cls(
            id=move_to_folder_item_id,
            display_name=resources.auto_process_item_name_move_to_folder,
            description=resources.auto_process_item_description_move_to_folder,
            action_type=2  # 2はMoveToFolderのアクションタイプ
        )
        # ExtractText
        extract_text_item = await cls.get_auto_process_item("extract_text")
        if extract_text_item is None:
            extract_text_item_id = "extract_text"
        else:
            extract_text_item_id = str(uuid.uuid4())
        extract_text_item = cls(
            id=extract_text_item_id,
            display_name=resources.auto_process_item_name_extract_text,
            description=resources.auto_process_item_description_extract_text,
            action_type=3  # 3はExtractTextのアクションタイプ
        )
        # PromptTemplate
        prompt_template_item = await cls.get_auto_process_item("prompt_template")
        if prompt_template_item is None:
            prompt_template_item_id = "prompt_template"
        else:
            prompt_template_item_id = str(uuid.uuid4())
        prompt_template_item = cls(
            id=prompt_template_item_id,
            display_name=resources.auto_process_item_name_prompt_template,
            description=resources.auto_process_item_description_prompt_template,
            action_type=4  # 4はPromptTemplateのアクションタイプ
        )
        # デフォルトの自動処理アイテムをデータベースに保存する
        for item in  [
            ignore_item,
            copy_to_folder_item,
            move_to_folder_item,
            extract_text_item,
            prompt_template_item
        ]:
            await cls.update_auto_process_item(item)


    @classmethod
    async def get_auto_process_items_api(cls, request_json: str) -> dict:
        items = await cls.get_auto_process_items()
        result: dict = {}
        result["auto_process_items"] = [item.dict() for item in items]
        return result
    
    @classmethod
    async def update_auto_process_items_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        items = await cls.get_auto_process_item_objects(request_dict)
        result: dict = {}
        result["auto_process_items"] = [await cls.update_auto_process_item(item) for item in items]
        return result
    
    @classmethod
    async def delete_auto_process_items_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        items = await cls.get_auto_process_item_objects(request_dict)
        result: dict = {}
        for item in items:
            await cls.delete_auto_process_item(item)
        result["deleted"] = True
        return result

    @classmethod
    async def get_auto_process_items(cls) -> list:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM AutoProcessItems")
                rows = await cur.fetchall()
                items = [cls(**dict(row)) for row in rows]
        return items
    
    @classmethod
    async def get_auto_process_item(cls, item_id: str) -> Optional["AutoProcessItem"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM AutoProcessItems WHERE id=?", (item_id,))
                row = await cur.fetchone()
                if row is None:
                    return None
                return cls(**dict(row))
    
    @classmethod
    async def update_auto_process_item(cls, item: "AutoProcessItem") -> "AutoProcessItem":
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                if await cls.get_auto_process_item(item.id) is None:
                    # 新規追加
                    await cur.execute("INSERT INTO AutoProcessItems (id, display_name, description, auto_process_item_type, action_type) VALUES (?, ?, ?, ?, ?)",
                                      (item.id, item.display_name, item.description, item.auto_process_item_type, item.action_type))
                else:
                    # 更新
                    await cur.execute("UPDATE AutoProcessItems SET display_name=?, description=?, auto_process_item_type=?, action_type=? WHERE id=?",
                                      (item.display_name, item.description, item.auto_process_item_type, item.action_type, item.id))
                await conn.commit()
        return item
    
    @classmethod
    async def delete_auto_process_item(cls, item: "AutoProcessItem") -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM AutoProcessItems WHERE id=?", (item.id,))
                await conn.commit()
