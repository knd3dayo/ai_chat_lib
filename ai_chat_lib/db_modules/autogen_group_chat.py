import sqlite3
import json
from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel, field_validator, Field
from typing import Optional, Union, List

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
    def get_autogen_group_chat_list_api(cls):
        group_chat_list = cls.get_autogen_group_chat_list()
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
    def get_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        group_chat_result = cls.get_autogen_group_chat(group_chat.name)
        result: dict = {}
        if group_chat_result:
            result["group_chat"] = group_chat_result.to_dict()
        return result

    @classmethod
    def update_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        cls.update_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_group_chat_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        group_chat = AutogenGroupChat.get_autogen_group_chat_object(request_dict)
        if not group_chat:
            raise ValueError("group_chat is not set")
        cls.delete_autogen_group_chat(group_chat)
        result: dict = {}
        return result

    def to_dict(self) -> dict:
        return self.model_dump()

    #################################################
    # AutogenGroupChat関連
    #################################################
    @classmethod
    def get_autogen_group_chat_list(cls) -> List["AutogenGroupChat"]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_group_chats")
        rows = cur.fetchall()
        group_chats = [AutogenGroupChat(**dict(row)) for row in rows]
        conn.close()

        return group_chats  

    @classmethod
    def get_autogen_group_chat(cls, group_chat_name: str) -> Union["AutogenGroupChat", None]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_group_chats WHERE name=?", (group_chat_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        group_chat_dict = dict(row)
        conn.close()

        return AutogenGroupChat(**group_chat_dict)

    @classmethod    
    def update_autogen_group_chat(cls, group_chat: "AutogenGroupChat"):
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        if cls.get_autogen_group_chat(group_chat.name) is None:
            cur.execute("INSERT INTO autogen_group_chats VALUES (?, ?, ?, ?)", 
                        (group_chat.name, group_chat.description, group_chat.llm_config_name, 
                         json.dumps(group_chat.agent_names, ensure_ascii=False)))
        else:
            cur.execute("UPDATE autogen_group_chats SET description=?, llm_config_name=?, agent_names_json=? WHERE name=?", 
                        (group_chat.description, group_chat.llm_config_name, 
                         json.dumps(group_chat.agent_names, ensure_ascii=False), group_chat.name))
        conn.commit()
        conn.close()

    @classmethod
    def delete_autogen_group_chat(cls, group_chat: "AutogenGroupChat"):
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_group_chats WHERE name=?", (group_chat.name,))
        conn.commit()
        conn.close()

    @classmethod    
    def init_autogen_group_chats_table(cls):
        # autogen_group_chatsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_group_chats (
                name TEXT PRIMARY KEY,
                description TEXT,
                llm_config_name TEXT,
                agent_names_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
        # デフォルトのautogen_group_chatsを初期化する
        cls.__init_default_autogen_group_chats()

    @classmethod
    def __init_default_autogen_group_chats(cls):
        import ai_chat_lib.resouces.resource_util as resource_util
        # デフォルトのautogen_group_chatsを初期化する
        string_resources = resource_util.get_string_resources()
        description = string_resources.autogen_default_group_chat_description
        default_group_chat = AutogenGroupChat(
            name="default_group_chat",
            description=description,
            llm_config_name="default",
            agent_names=["planner"]
        )
        cls.update_autogen_group_chat(default_group_chat)
