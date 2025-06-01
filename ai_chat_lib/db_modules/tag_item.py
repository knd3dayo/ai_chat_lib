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

from ai_chat_lib.db_modules.main_db import MainDB

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
        tag_items = cls.get_tag_items()
        result: dict = {}
        result["tag_items"] = [item.dict() for item in tag_items]
        return result

    @classmethod
    def update_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = TagItem.get_tag_item_objects(request_dict)
        for tag_item in tag_items:
            cls.update_tag_item(tag_item)
        result: dict = {}
        return result

    @classmethod
    def delete_tag_items_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tag_items = TagItem.get_tag_item_objects(request_dict)
        for tag_item in tag_items:
            cls.delete_tag_item(tag_item)
        result: dict = {}
        return result

    def to_dict(self) -> dict:
        return self.dict()

    @classmethod
    def get_tag_item(cls, tag_id: str) -> Union["TagItem", None]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
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
    
    @classmethod
    def get_tag_items(cls) -> List["TagItem"]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM TagItems")
        rows = cur.fetchall()
        tag_items = [TagItem(**dict(row)) for row in rows]
        conn.close()

        return tag_items
    
    @classmethod
    def update_tag_item(cls, tag_item: "TagItem") -> "TagItem":
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        if cls.get_tag_item(tag_item.id) is None:
            cur.execute("INSERT INTO TagItems VALUES (?, ?, ?)", (tag_item.id, tag_item.tag, tag_item.is_pinned))
        else:
            cur.execute("UPDATE TagItems SET tag=?, is_pinned=? WHERE id=?", (tag_item.tag, tag_item.is_pinned, tag_item.id))
        conn.commit()
        conn.close()

        # 更新したTagItemを返す
        return tag_item
    
    @classmethod
    def delete_tag_item(cls, tag_item: "TagItem"):
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("DELETE FROM TagItems WHERE id=?", (tag_item.id,))
        conn.commit()
        conn.close()


    @classmethod
    def init_tag_item_table(cls):
        # TagItemsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(MainDB.get_main_db_path())
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
