import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
import uuid
import os
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from typing import Optional
from typing import Optional, Union, List
from typing import Optional, List, Union

from ai_chat_lib.db_modules.main_db import MainDB
from vector_search_mcp.model.models import VectorDBItemBase
import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class VectorDBItem(VectorDBItemBase):
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

    @classmethod    
    async def create_table(cls):
        # VectorDBItemsテーブルが存在しない場合は作成する
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute('''
                    SELECT name FROM sqlite_master WHERE type="table" AND name="VectorDBItems"
                ''')
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("VectorDBItems table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating VectorDBItems table.")
                    await cur.execute('''
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
                    await conn.commit()

                    await cls.update_default_data()

    @classmethod
    async def update_default_data(cls):
        # name="default"のVectorDBItemを取得
        vector_db_item = await VectorDBItem.get_vector_db_by_name("default")
        # 存在しない場合は初期化処理
        if not vector_db_item:
            # VectorDBItemを作成
            params = {
                "id": str(uuid.uuid4()),
                "name": "default",
                "description": "Application default vector db",
                "vector_db_url": os.path.join(os.getenv("APP_DATA_PATH", ""), "server", "vector_db", "default_vector_db"),
                # multi_vector_retrieverは廃止
                "is_use_multi_vector_retriever": False,
                "doc_store_url": "",
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
            await cls.update_vector_db_item(vector_db_item)

        else:
            # 存在する場合は初期化処理を行わない
            logger.info("VectorDBItem is already exists.")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    default_search_result_limit: int = 10
    default_score_threshold: float = 0.5
    is_enabled: bool = False
    is_system: bool = False
    system_message: Optional[str] = None
    folder_id: Optional[str] = ""


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


    # Idを指定してVectorDBItemのdictを取得する
    @classmethod
    async def get_vector_db_item_dict_by_id(cls, vector_db_item_id: str) -> Union[dict, None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM VectorDBItems WHERE id=?", (vector_db_item_id,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                vector_db_item_dict = dict(row)

        return vector_db_item_dict

    # Idを指定してVectorDBItemを取得する
    @classmethod
    async def get_vector_db_by_id(cls, vector_db_item_id: str) -> Union["VectorDBItem", None]:
        vector_db_item_dict = await cls.get_vector_db_item_dict_by_id(vector_db_item_id)
        if vector_db_item_dict is None:
            return None
        return VectorDBItem(**vector_db_item_dict)

    # nameを指定してVectorDBItemのdictを取得する
    @classmethod
    async def get_vector_db_item_dict_by_name(cls, vector_db_item_name: str) -> Union[dict, None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM VectorDBItems WHERE name=?", (vector_db_item_name,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                vector_db_item_dict = dict(row)

        return vector_db_item_dict

    # Nameを指定してVectorDBItemを取得する
    @classmethod
    async def get_vector_db_by_name(cls, vector_db_item_name: str) -> Union["VectorDBItem", None]:
        vector_db_item_dict = await cls.get_vector_db_item_dict_by_name(vector_db_item_name)
        if vector_db_item_dict is None:
            return None
        return VectorDBItem(**vector_db_item_dict)
    
    @classmethod
    async def get_vector_db_items(cls) -> List["VectorDBItem"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM VectorDBItems")
                rows = await cur.fetchall()
                vector_db_items = [VectorDBItem(**dict(row)) for row in rows]

        return vector_db_items
    
    # folder_idを指定してパスを取得する
    @classmethod
    async def get_vector_db_item_path(cls, vector_db_item_id: str) -> str:
        vector_db_item = await cls.get_vector_db_by_id(vector_db_item_id)
        if vector_db_item is None:
            raise ValueError("VectorDBItem not found")
        return vector_db_item.vector_db_url

    @classmethod
    async def update_vector_db_item(cls, vector_db_item: "VectorDBItem") -> "VectorDBItem":
        if not vector_db_item.vector_db_type:
            raise ValueError("vector_db_type must be 1:Chroma or 2:PGVector")

        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                if await cls.get_vector_db_by_id(vector_db_item.id) is None:
                    await cur.execute("INSERT INTO VectorDBItems VALUES (?, ? , ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                (vector_db_item.id, vector_db_item.name, vector_db_item.description, 
                                # multi_vector_retrieverは廃止
                                vector_db_item.vector_db_url, False, "", 
                                vector_db_item.vector_db_type, 
                                vector_db_item.collection_name, 
                                vector_db_item.chunk_size, vector_db_item.default_search_result_limit, 
                                vector_db_item.default_score_threshold,
                                vector_db_item.is_enabled, vector_db_item.is_system)
                                )
                else:
                    await cur.execute("UPDATE VectorDBItems SET name=?, description=?, vector_db_url=?, is_use_multi_vector_retriever=?, doc_store_url=?, vector_db_type=?, collection_name=?, chunk_size=?, default_search_result_limit=?, default_score_threshold=?, is_enabled=?, is_system=? WHERE id=?",
                                (vector_db_item.name, vector_db_item.description, vector_db_item.vector_db_url, 
                                 # multi_vector_retrieverは廃止
                                False, "", 
                                vector_db_item.vector_db_type, vector_db_item.collection_name, 
                                vector_db_item.chunk_size, 
                                vector_db_item.default_search_result_limit, 
                                vector_db_item.default_score_threshold,                          
                                vector_db_item.is_enabled, 
                                vector_db_item.is_system, vector_db_item.id)
                                )
                await conn.commit()

        # 更新したVectorDBItemを返す
        return vector_db_item

    @classmethod
    async def delete_vector_db_item(cls, vector_db_item: "VectorDBItem"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            await cur.execute("DELETE FROM VectorDBItems WHERE id=?", (vector_db_item.id,))
            await conn.commit()
