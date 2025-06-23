import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel, field_validator, Field
from typing import Optional, Union, List
import ai_chat_lib.resouces.resource_util as resource_util

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.main_db import MainDB


class AutogenGroupChat(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_group_chats (name TEXT, description TEXT, llm_config_name TEXT, agent_names_json TEXT)
    '''
    name: str = ""
    description: str = ""
    llm_config_name: str = ""
    agent_names: list = Field(default_factory=list)
    agent_names_json: Optional[str] = None

    @field_validator("agent_names", mode="before")
    @classmethod
    def parse_agent_names(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("agent_names_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return []

    @classmethod
    async def get_autogen_group_chat_list_api(cls):
        group_chat_list = await cls.get_autogen_group_chat_list()
        if not group_chat_list:
            raise ValueError("group_chat_list is not set")
        result = {}
        result["group_chat_list"] = [group_chat.to_dict() for group_chat in group_chat_list]
        return result

    autogen_group_chat_request_name: ClassVar[str] = "autogen_group_chat_request"

    @classmethod
    def get_autogen_group_chat_object(cls, request_dict: dict) -> "AutogenGroupChat":
        request: Optional[dict] = request_dict.get(cls.autogen_group_chat_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenGroupChat(**request)

    @classmethod
    async def get_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        group_chat_result = await cls.get_autogen_group_chat(group_chat.name)
        result: dict = {}
        if group_chat_result:
            result["group_chat"] = group_chat_result.to_dict()
        return result

    @classmethod
    async def update_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        await cls.update_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    @classmethod
    async def delete_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        await cls.delete_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    def to_dict(self) -> dict:
        return self.model_dump()

    #################################################
    # AutogenGroupChat関連
    #################################################
    @classmethod
    async def get_autogen_group_chat_list(cls) -> List["AutogenGroupChat"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_group_chats")
                rows = await cur.fetchall()
                group_chats = [AutogenGroupChat(**dict(row)) for row in rows]

        return group_chats  

    @classmethod
    async def get_autogen_group_chat(cls, group_chat_name: str) -> Union["AutogenGroupChat", None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_group_chats WHERE name=?", (group_chat_name,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                group_chat_dict = dict(row)

        return AutogenGroupChat(**group_chat_dict)

    @classmethod    
    async def update_autogen_group_chat(cls, group_chat: "AutogenGroupChat"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            if await cls.get_autogen_group_chat(group_chat.name) is None:
                await cur.execute("INSERT INTO autogen_group_chats VALUES (?, ?, ?, ?)", 
                                  (group_chat.name, group_chat.description, group_chat.llm_config_name, 
                                   json.dumps(group_chat.agent_names, ensure_ascii=False)))
            else:
                await cur.execute("UPDATE autogen_group_chats SET description=?, llm_config_name=?, agent_names_json=? WHERE name=?", 
                                  (group_chat.description, group_chat.llm_config_name, 
                                   json.dumps(group_chat.agent_names, ensure_ascii=False), group_chat.name))
            await conn.commit()

    @classmethod
    async def delete_autogen_group_chat(cls, group_chat: "AutogenGroupChat"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            await cur.execute("DELETE FROM autogen_group_chats WHERE name=?", (group_chat.name,))
            await conn.commit()

    @classmethod    
    async def create_table(cls):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # autogen_group_chatsテーブルが存在しない場合は作成する
                rows = await cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autogen_group_chats'")
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.info("autogen_group_chats table already exists.")
                    return
                else:
                    logger.info("Creating autogen_group_chats table.")
                    # テーブルが存在しない場合は作成する
                    await cur.execute('''
                        CREATE TABLE IF NOT EXISTS autogen_group_chats (
                            name TEXT PRIMARY KEY,
                            description TEXT,
                            llm_config_name TEXT,
                            agent_names_json TEXT
                        )
                    ''')
                    await conn.commit()

                    # デフォルトのautogen_group_chatsを初期化する
                    await cls.update_default_data()

    @classmethod
    async def update_default_data(cls):
        # デフォルトのautogen_group_chatsを初期化する
        string_resources = resource_util.get_string_resources()
        description = string_resources.autogen_default_group_chat_description
        default_group_chat = AutogenGroupChat(
            name="default",
            description=description,
            llm_config_name="default",
            agent_names=["planner"]
        )
        await cls.update_autogen_group_chat(default_group_chat)
