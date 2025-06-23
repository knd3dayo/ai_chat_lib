import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)
from ai_chat_lib.db_modules.main_db import MainDB

class AutogenTools(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_tools (name TEXT, path TEXT, description TEXT)
    '''
    name: str = ""
    path: str = ""
    description: str = ""

    @classmethod
    async def get_autogen_tool_list_api(cls):
        tools_list = await cls.get_autogen_tool_list()
        result = {}
        result["tool_list"] = [tool.to_dict() for tool in tools_list]
        return result

    @classmethod
    async def get_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        tool_result = await cls.get_autogen_tool(tool.name)
        result: dict = {}
        if tool_result:
            result["tool"] = tool_result.to_dict()
        return result

    @classmethod
    async def update_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        await cls.update_autogen_tool(tool)
        result: dict = {}
        return result

    @classmethod
    async def delete_autogen_tool_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        tool = AutogenTools.get_autogen_tool_object(request_dict)
        if not tool:
            raise ValueError("tool is not set")
        await cls.delete_autogen_tool(tool)
        result: dict = {}
        return result

    autogen_tool_request_name: ClassVar[str] = "autogen_tool_request"

    @classmethod
    def get_autogen_tool_object(cls, request_dict: dict) -> "AutogenTools":
        '''
        {"autogen_tool_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.autogen_tool_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenTools(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    async def get_autogen_tool(cls, tool_name: str) -> Union["AutogenTools", None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_tools WHERE name=?", (tool_name,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                tool_dict = dict(row)

        return AutogenTools(**tool_dict)
    
    @classmethod
    async def get_autogen_tool_list(cls) -> List["AutogenTools"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_tools")
                rows = await cur.fetchall()
                tools = [AutogenTools(**dict(row)) for row in rows]

        return tools

    @classmethod
    async def update_autogen_tool(cls, tool: "AutogenTools"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            if await cls.get_autogen_tool(tool.name) is None:
                await cur.execute("INSERT INTO autogen_tools VALUES (?, ?, ?)", (tool.name, tool.path, tool.description))
            else:
                await cur.execute("UPDATE autogen_tools SET path=?, description=? WHERE name=?", (tool.path, tool.description, tool.name))
            await conn.commit()

    @classmethod
    async def delete_autogen_tool(cls, tool: "AutogenTools"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            await cur.execute("DELETE FROM autogen_tools WHERE name=?", (tool.name,))
            await conn.commit()


    @classmethod
    async def create_table(cls):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='autogen_tools'")
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("autogen_tools table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating autogen_tools table.")
                    await cur.execute('''
                        CREATE TABLE IF NOT EXISTS autogen_tools (
                            name TEXT PRIMARY KEY,
                            path TEXT,
                            description TEXT
                        )
                    ''')
                    await conn.commit()
                    # Initialize the autogen_tools table
                    await cls.update_default_data()
        
    @classmethod
    async def update_default_data(cls):
        # デフォルトのautogen_toolsを登録する
        import importlib.util

        # search_wikipedia_ja
        module_name = "ai_chat_lib.autogen_modules.search_wikipedia_ja"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function searches Wikipedia with the specified keywords and returns related articles."
            tool = AutogenTools(name="search_wikipedia_ja", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)

        # list_files_in_directory
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function lists files in the specified directory."
            tool = AutogenTools(name="list_files_in_directory", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)
        
        # extract_file in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function extracts files in the specified directory."
            tool = AutogenTools(name="extract_file", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)
    
        # check_file in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function checks the existence of a file in the specified directory."
            tool = AutogenTools(name="check_file", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)

        # extract_webpage in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function extracts text from a webpage."
            tool = AutogenTools(name="extract_webpage", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)

        # search_duckduckgo in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function searches DuckDuckGo with the specified keywords and returns related articles."
            tool = AutogenTools(name="search_duckduckgo", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)

        # save_text_file in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function saves text to a file."
            tool = AutogenTools(name="save_text_file", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)
        
        # arxiv_search in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function searches arXiv with the specified keywords and returns related articles."
            tool = AutogenTools(name="arxiv_search", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)
        
        # get_current_time in default_tools
        module_name = "ai_chat_lib.autogen_modules.default_tools"
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            description = "This function returns the current time."
            tool = AutogenTools(name="get_current_time", path=spec.origin, description=description)
            await cls.update_autogen_tool(tool)
        