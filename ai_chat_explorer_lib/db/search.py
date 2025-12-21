from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
import json
import uuid
from ai_chat_explorer_lib.resouces.resource_util import get_string_resources
from ai_chat_explorer_lib.db.main_db import MainDB

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

"""
以下のフィールドを持つPydanticモデルを定義します。
description: str
content: str
tags: str
source_application_name: str
source_application_title: str
start_time_str: str
end_time_str: str
enable_start_time: bool
enable_end_time: bool
exclude_description: bool
exclude_content: bool
exclude_tags: bool
exclude_source_application_name: bool
exclude_source_application_title: bool
"""
class SearchCondition(BaseModel):
    description: str
    content: str
    tags: str
    source_application_name: str
    source_application_title: str
    start_time_str: str
    end_time_str: str
    enable_start_time: bool
    enable_end_time: bool
    exclude_description: bool
    exclude_content: bool
    exclude_tags: bool
    exclude_source_application_name: bool
    exclude_source_application_title: bool

from typing import Optional, Union, Sequence
from pydantic import BaseModel, Field
import aiosqlite
import uuid

import ai_chat_explorer_lib.model as model_base
from ai_chat_explorer_lib.resouces import *
from ai_chat_explorer_lib.db.main_db import MainDB

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class SearchRule(model_base.SearchRuleModel):
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
    async def update_search_rule(cls, search_rule: model_base.SearchRuleModel) -> model_base.SearchRuleModel:
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
    async def update_search_rules(cls, search_rules: Sequence[model_base.SearchRuleModel]) -> Sequence[model_base.SearchRuleModel]:
        updated_rules = []
        for rule in search_rules:
            updated_rule = await cls.update_search_rule(rule)
            updated_rules.append(updated_rule)
        return updated_rules
    
    @classmethod
    async def delete_search_rule(cls, search_rule: model_base.SearchRuleModel) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            await cur.execute("DELETE FROM SearchRules WHERE id=?", (search_rule.id,))
            await conn.commit()
    
    @classmethod
    async def delete_search_rules(cls, search_rules: Sequence[model_base.SearchRuleModel]) -> None:
        for rule in search_rules:
            await cls.delete_search_rule(rule)