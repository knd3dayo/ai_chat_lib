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

import ai_chat_lib.log_modules.log_settings as log_settings
from ai_chat_lib.db_modules.main_db import MainDB
logger = log_settings.getLogger(__name__)

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

    @classmethod    
    async def init_vector_db_item_table(cls):
        # VectorDBItemsテーブルが存在しない場合は作成する
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
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

        await cls.__init_default_vector_db_item()

    @classmethod
    async def __init_default_vector_db_item(cls):
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
            await cls.update_vector_db_item(vector_db_item)

        else:
            # 存在する場合は初期化処理を行わない
            logger.info("VectorDBItem is already exists.")

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
    async def update_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = VectorDBItem.get_vector_db_item_object(request_dict)
        await cls.update_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    async def delete_vector_db_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_item = VectorDBItem.get_vector_db_item_object(request_dict)
        await cls.delete_vector_db_item(vector_db_item)
        result: dict = {}
        result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    async def get_vector_db_items_api(cls):
        vector_db_list = await cls.get_vector_db_items()
        result = {}
        result["vector_db_items"] = [item.to_dict() for item in vector_db_list]
        return result

    @classmethod
    async def get_vector_db_item_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_id = VectorDBItem.get_vector_db_item_object(request_dict).id
        if not vector_db_id:
            raise ValueError("vector_db_id is not set")
        vector_db_item = await cls.get_vector_db_by_id(vector_db_id)
        result: dict = {}
        if vector_db_item is not None:
            result["vector_db_item"] = vector_db_item.to_dict()
        return result

    @classmethod
    async def get_vector_db_item_by_name_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        vector_db_name = VectorDBItem.get_vector_db_item_object(request_dict).name
        if not vector_db_name:
            raise ValueError("vector_db_name is not set")
        vector_db = await cls.get_vector_db_by_name(vector_db_name)
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
                                vector_db_item.vector_db_url, vector_db_item.is_use_multi_vector_retriever, 
                                vector_db_item.doc_store_url, vector_db_item.vector_db_type, 
                                vector_db_item.collection_name, 
                                vector_db_item.chunk_size, vector_db_item.default_search_result_limit, 
                                vector_db_item.default_score_threshold,
                                vector_db_item.is_enabled, vector_db_item.is_system)
                                )
                else:
                    await cur.execute("UPDATE VectorDBItems SET name=?, description=?, vector_db_url=?, is_use_multi_vector_retriever=?, doc_store_url=?, vector_db_type=?, collection_name=?, chunk_size=?, default_search_result_limit=?, default_score_threshold=?, is_enabled=?, is_system=? WHERE id=?",
                                (vector_db_item.name, vector_db_item.description, vector_db_item.vector_db_url, 
                                vector_db_item.is_use_multi_vector_retriever, vector_db_item.doc_store_url, 
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
