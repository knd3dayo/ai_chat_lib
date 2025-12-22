from typing import Optional, Sequence
import uuid

import aiosqlite
import ai_chat_explorer_lib.model as model_base

from ai_chat_explorer_lib.resouces.resource_util import *
from ai_chat_explorer_lib.db.main_db import MainDB

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AutoProcessItem(model_base.AutoProcessItemModel):
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
 
    @classmethod
    async def create_table(cls) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute('''
                    SELECT name FROM sqlite_master WHERE type="table" AND name="AutoProcessItems"
                ''')
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("AutoProcessItems table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating AutoProcessItems table.")
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
        resources = get_string_resources()

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
    async def get_auto_process_items(cls) -> Sequence[model_base.AutoProcessItemModel]:
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
    async def update_auto_process_item(cls, item: model_base.AutoProcessItemModel) -> model_base.AutoProcessItemModel:
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
    async def update_auto_process_items(cls, items: Sequence[model_base.AutoProcessItemModel]) -> Sequence[model_base.AutoProcessItemModel]:
        updated_items = []
        for item in items:
            updated_item = await cls.update_auto_process_item(item)
            updated_items.append(updated_item)
        return updated_items
        
    @classmethod
    async def delete_auto_process_item(cls, item: model_base.AutoProcessItemModel) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM AutoProcessItems WHERE id=?", (item.id,))
                await conn.commit() 

    @classmethod
    async def delete_auto_process_items(cls, items: Sequence[model_base.AutoProcessItemModel]) -> None:
        for item in items:
            await cls.delete_auto_process_item(item)

from typing import Optional, Sequence
from pydantic import BaseModel, Field
import aiosqlite
import uuid

import ai_chat_explorer_lib.model as model_base
from ai_chat_explorer_lib.resouces import *
from ai_chat_explorer_lib.db.main_db import MainDB
import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AutoProcessRule(model_base.AutoProcessRuleModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "AutoProcessRules" (
        "id" TEXT NOT NULL CONSTRAINT "PK_AutoProcessRules" PRIMARY KEY,
        "rule_name" TEXT NOT NULL,
        "is_enabled" INTEGER NOT NULL,
        "priority" INTEGER NOT NULL,
        "conditions_json" TEXT NOT NULL,
        "auto_process_item_id" TEXT NULL,
        "target_folder_id" TEXT NULL,
        "destination_folder_id" TEXT NULL
    )
    '''
    
    @classmethod
    async def create_table(cls) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute('''
                    SELECT name FROM sqlite_master WHERE type="table" AND name="auto_process_rules"
                ''')
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("auto_process_rules table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating auto_process_rules table.")
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS "auto_process_rules" (
                            "id" TEXT NOT NULL CONSTRAINT "PK_auto_process_rules" PRIMARY KEY,
                            "rule_name" TEXT NOT NULL,
                            "is_enabled" INTEGER NOT NULL,
                            "priority" INTEGER NOT NULL,
                            "conditions_json" TEXT NOT NULL,
                            "auto_process_item_id" TEXT NULL,
                            "target_folder_id" TEXT NULL,
                            "destination_folder_id" TEXT NULL
                        )
                    ''')
                    await conn.commit()

    @classmethod
    async def get_auto_process_rules(cls) -> list:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM auto_process_rules")
                rows = await cur.fetchall()
                rules = [cls(**dict(row)) for row in rows]
        return rules    
    
    @classmethod
    async def get_auto_process_rule(cls, rule_id: str) -> Optional["AutoProcessRule"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM auto_process_rules WHERE id=?", (rule_id,))
                row = await cur.fetchone()
                if row is None:
                    return None
                return cls(**dict(row))
            
    @classmethod
    async def update_auto_process_rule(cls, rule: model_base.AutoProcessRuleModel) -> model_base.AutoProcessRuleModel:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                if await cls.get_auto_process_rule(rule.id) is None:
                    await cur.execute("INSERT INTO auto_process_rules (id, rule_name, is_enabled, priority, conditions_json, auto_process_item_id, target_folder_id, destination_folder_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                                      (rule.id, rule.rule_name, int(rule.is_enabled), rule.priority, rule.conditions_json, rule.auto_process_item_id, rule.target_folder_id, rule.destination_folder_id))
                else:
                    await cur.execute("UPDATE auto_process_rules SET rule_name=?, is_enabled=?, priority=?, conditions_json=?, auto_process_item_id=?, target_folder_id=?, destination_folder_id=? WHERE id=?", 
                                      (rule.rule_name, int(rule.is_enabled), rule.priority, rule.conditions_json, rule.auto_process_item_id, rule.target_folder_id, rule.destination_folder_id, rule.id))
                await conn.commit()
        return rule
    
    @classmethod
    async def update_auto_process_rules(cls, rules: Sequence[model_base.AutoProcessRuleModel]) -> Sequence[model_base.AutoProcessRuleModel]:
        updated_rules = []
        for rule in rules:
            updated_rule = await cls.update_auto_process_rule(rule)
            updated_rules.append(updated_rule)
        return updated_rules

    @classmethod
    async def delete_auto_process_rule(cls, rule: model_base.AutoProcessRuleModel) -> None:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM auto_process_rules WHERE id=?", (rule.id,))
                await conn.commit()
    
    @classmethod
    async def delete_auto_process_rules(cls, rules: Sequence[model_base.AutoProcessRuleModel]) -> None:
        for rule in rules:
            await cls.delete_auto_process_rule(rule)