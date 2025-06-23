from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
import json
import uuid
from ai_chat_lib.resouces import *
from ai_chat_lib.db_modules.main_db import MainDB

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class SearchRule(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "SearchRules" (
    "id" TEXT NOT NULL CONSTRAINT "PK_SearchRules" PRIMARY KEY,
    "name" TEXT NOT NULL,
    "search_condition_json" TEXT NOT NULL,
    "search_folder_id" TEXT NULL,
    "target_folder_id" TEXT NULL,
    "is_include_sub_folder" INTEGER NOT NULL,
    "is_global_search" INTEGER NOT NULL
    )
    PromptItem,AutoProcessItem,AutoProcessRule,TagItemなどと同様にAPIを提供する
    '''
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the search rule")
    name: str = Field(..., description="Name of the search rule")
    search_condition_json: str = Field(..., description="JSON string representing the search conditions")
    is_include_sub_folder: bool = Field(default=False, description="Whether to include subfolders in the search")
    is_global_search: bool = Field(default=False, description="Whether the search is a global search")
    search_folder_id: Optional[str] = Field(None, description="ID of the folder to search in")
    target_folder_id: Optional[str] = Field(None, description="ID of the target folder for the search results")

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
            search_rule = cls(**item)
            search_rules.append(search_rule)
        return search_rules
    
    @classmethod
    async def create_table(cls) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute('''
                    SELECT name FROM sqlite_master WHERE type="table" AND name="SearchRules"
                ''')
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("SearchRules table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating SearchRules table.")
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS "SearchRules" (
                            "id" TEXT NOT NULL CONSTRAINT "PK_SearchRules" PRIMARY KEY,
                            "name" TEXT NOT NULL,
                            "search_condition_json" TEXT NOT NULL,
                            "search_folder_id" TEXT NULL,
                            "target_folder_id" TEXT NULL,
                            "is_include_sub_folder" INTEGER NOT NULL,
                            "is_global_search" INTEGER NOT NULL
                        )
                    ''')
                    await conn.commit()
    @classmethod
    async def get_search_rules_api(cls, request_json: str) -> dict:
        search_rules = await cls.get_search_rules()
        result: dict = {}
        result["search_rules"] = [search_rule.to_dict() for search_rule in search_rules]

        return result
        
    @classmethod
    async def update_search_rules_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        search_rules = await cls.get_search_rule_objects(request_dict)
        for search_rule in search_rules:
            await cls.update_search_rule(search_rule)
        result: dict = {}
        return result
    @classmethod
    async def delete_search_rules_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        search_rules = await cls.get_search_rule_objects(request_dict)
        for search_rule in search_rules:
            await cls.delete_search_rule(search_rule)
        result: dict = {}
        return result
    
    def to_dict(self) -> dict:
        return self.model_dump() 
    
    @classmethod
    async def get_search_rules(cls) -> list["SearchRule"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM SearchRules")
                rows = await cur.fetchall()
                search_rules = [SearchRule(**dict(row)) for row in rows]
        return search_rules
    
    @classmethod
    async def get_search_rule(cls, search_rule_id: str) -> Union["SearchRule", None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM SearchRules WHERE id=?", (search_rule_id,))
                row = await cur.fetchone()
                if row is None or len(row) == 0:
                    return None
                search_rule_dict = dict(row)
        return SearchRule(**search_rule_dict)
    
    @classmethod
    async def update_search_rule(cls, search_rule: "SearchRule") -> "SearchRule":
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            if await cls.get_search_rule(search_rule.id) is None:
                # 新規追加
                await cur.execute('''
                    INSERT INTO SearchRules (id, name, search_condition_json, search_folder_id, target_folder_id, is_include_sub_folder, is_global_search)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (search_rule.id, search_rule.name, search_rule.search_condition_json, search_rule.search_folder_id, search_rule.target_folder_id, int(search_rule.is_include_sub_folder), int(search_rule.is_global_search)))
            else:
                # 更新
                await cur.execute('''
                    UPDATE SearchRules SET name=?, search_condition_json=?, search_folder_id=?, target_folder_id=?, is_include_sub_folder=?, is_global_search=?
                    WHERE id=?
                ''', (search_rule.name, search_rule.search_condition_json, search_rule.search_folder_id, search_rule.target_folder_id, int(search_rule.is_include_sub_folder), int(search_rule.is_global_search), search_rule.id))
            await conn.commit()
        return search_rule
    @classmethod
    async def delete_search_rule(cls, search_rule: "SearchRule") -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            await cur.execute("DELETE FROM SearchRules WHERE id=?", (search_rule.id,))
            await conn.commit()
    