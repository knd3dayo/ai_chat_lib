import sqlite3
import json
from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel, field_validator
from typing import Optional, Union, List

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.main_db import MainDB

class AutogenAgent(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_agents (
        name TEXT PRIMARY KEY, description TEXT, system_message TEXT, 
        code_execution INTEGER, llm_config_name TEXT, tool_names_json TEXT, vector_db_items_json TEXT)
    '''
    name: str = ""
    description: str = ""
    system_message: str = ""
    code_execution: bool = False
    llm_config_name: str = ""
    tool_names: Union[str, list, None] = ""
    vector_db_items: Union[list, None] = []
    tool_names_json: Optional[str] = None
    vector_db_items_json: Optional[str] = None

    @field_validator("code_execution", mode="before")
    @classmethod
    def parse_code_execution(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @field_validator("tool_names", mode="before")
    @classmethod
    def parse_tool_names(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("tool_names_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return ""

    @field_validator("vector_db_items", mode="before")
    @classmethod
    def parse_vector_db_items(cls, v, values):
        if v is not None and v != "":
            return v
        json_val = values.get("vector_db_items_json", None)
        if json_val:
            try:
                return json.loads(json_val)
            except Exception:
                return json_val
        return []

    @classmethod
    def get_autogen_agent_list_api(cls):
        agent_list = cls.get_autogen_agent_list()
        if not agent_list:
            raise ValueError("agent_list is not set")
        result = {}
        result["agent_list"] = [agent.to_dict() for agent in agent_list]
        return result

    @classmethod
    def get_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        agent_result = cls.get_autogen_agent(agent.name)
        result: dict = {}
        if agent_result:
            result["agent"] = agent_result.to_dict()
        return result

    @classmethod
    def update_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        cls.update_autogen_agent(agent)
        result: dict = {}
        return result

    @classmethod
    def delete_autogen_agent_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        agent = AutogenAgent.get_autogen_agent_object(request_dict)
        if not agent:
            raise ValueError("agent is not set")
        cls.delete_autogen_agent(agent)
        result: dict = {}
        return result

    autogen_agent_request_name: ClassVar[str] = "autogen_agent_request"

    @classmethod
    def get_autogen_agent_object(cls, request_dict: dict) -> "AutogenAgent":
        request: Optional[dict] = request_dict.get(cls.autogen_agent_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenAgent(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def get_autogen_agent_list(cls) -> List["AutogenAgent"]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_agents")
        rows = cur.fetchall()
        agents = [AutogenAgent(**dict(row)) for row in rows]
        conn.close()

        return agents

    @classmethod
    def get_autogen_agent(cls, agent_name: str) -> Union["AutogenAgent", None]:
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM autogen_agents WHERE name=?", (agent_name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None
        agent_dict = dict(row)
        conn.close()

        return AutogenAgent(**agent_dict)
    
    @classmethod
    def update_autogen_agent(cls, agent: "AutogenAgent"):
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        if cls.get_autogen_agent(agent.name) is None:
            cur.execute("INSERT INTO autogen_agents VALUES (?, ?, ?, ?, ?, ?, ?)", 
                        (agent.name, agent.description, agent.system_message, 
                         agent.code_execution, agent.llm_config_name, 
                         json.dumps(agent.tool_names, ensure_ascii=False), 
                         json.dumps(agent.vector_db_items,ensure_ascii=False)))
        else:
            cur.execute("UPDATE autogen_agents SET description=?, system_message=?, code_execution=?, llm_config_name=?, tool_names_json=?, vector_db_items_json=? WHERE name=?", 
                        (agent.description, agent.system_message, 
                         agent.code_execution, agent.llm_config_name, 
                         json.dumps(agent.tool_names, ensure_ascii=False), 
                         json.dumps(agent.vector_db_items,ensure_ascii=False), 
                         agent.name))
        conn.commit()
        conn.close()
    
    @classmethod
    def delete_autogen_agent(cls, agent: "AutogenAgent"):
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute("DELETE FROM autogen_agents WHERE name=?", (agent.name,))
        conn.commit()
        conn.close()


    @classmethod
    def init_autogen_agents_table(cls):
        # autogen_agentsテーブルが存在しない場合は作成する
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS autogen_agents (
                name TEXT PRIMARY KEY,
                description TEXT,
                system_message TEXT,
                code_execution INTEGER,
                llm_config_name TEXT,
                tool_names_json TEXT,
                vector_db_items_json TEXT
            )
        ''')
        conn.commit()
        conn.close()
        cls.__init_default_agent()

    @classmethod
    def __init_default_agent(cls):
        import ai_chat_lib.resouces.resource_util as resource_util

        string_resources = resource_util.get_string_resources()
        # default agentを登録する
        description = string_resources.autogen_planner_agent_description
        system_message = string_resources.autogen_planner_agent_system_message

        autogen_agent = AutogenAgent(
            name="planner",
            description=description,
            system_message=system_message,
            code_execution=True,
            llm_config_name="default",
            tool_names=[],
            vector_db_items=[]
        )
        cls.update_autogen_agent(autogen_agent)
        logger.info("Default autogen agent 'planner' has been initialized.")