from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
from ai_chat_lib.resouces import *
from ai_chat_lib.db_modules.main_db import MainDB
import json
import uuid
import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class AutoProcessRule(BaseModel):
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
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the auto process rule")
    rule_name : str = Field(..., description="Name of the auto process rule")
    is_enabled: bool = Field(default=True, description="Whether the rule is enabled or not")
    priority: int = Field(default=0, description="Priority of the rule, lower numbers indicate higher priority")
    conditions_json: str = Field(..., description="JSON string representing the conditions for the rule")
    auto_process_item_id: Optional[str] = Field(None, description="ID of the auto process item associated with the rule")
    target_folder_id: Optional[str] = Field(None, description="ID of the target folder for the rule")
    destination_folder_id: Optional[str] = Field(None, description="ID of the destination folder for the rule")
    
    auto_process_rule_requests_name: ClassVar[str] = "auto_process_rule_requests"
    @classmethod
    async def get_auto_process_rule_objects(cls, request_dict: dict) -> list:
        '''
        {"auto_process_rule_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[list[dict], None] = request_dict.get(cls.auto_process_rule_requests_name, None)
        if not request:
            logger.info("auto process rule request is not set. skipping.")
            return []
        auto_process_rules = []
        for item in request:
            auto_process_rule = cls(**item)
            auto_process_rules.append(auto_process_rule)
        return auto_process_rules
    
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
    async def get_auto_process_rules_api(cls, request_json: str) -> dict:
        rules = await cls.get_auto_process_rules()
        result: dict = {}
        result["auto_process_rules"] = [rule.dict() for rule in rules]
        return result
    
    @classmethod
    async def update_auto_process_rules_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        rules = await cls.get_auto_process_rule_objects(request_dict)
        result: dict = {}
        result["auto_process_rules"] = [await cls.update_auto_process_rule(rule) for rule in rules]
        return result
    
    @classmethod
    async def delete_auto_process_rules_api(cls, request_json: str) -> dict:
        request_dict = json.loads(request_json)
        rules = await cls.get_auto_process_rule_objects(request_dict)
        result: dict = {}
        for rule in rules:
            await cls.delete_auto_process_rule(rule)
        result["deleted"] = True
        return result
    
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
    async def update_auto_process_rule(cls, rule: "AutoProcessRule") -> "AutoProcessRule":
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
    async def delete_auto_process_rule(cls, rule: "AutoProcessRule"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM auto_process_rules WHERE id=?", (rule.id,))
                await conn.commit()