import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel, Field
from typing import Optional, List, Union

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.main_db import MainDB

class AutogenLLMConfig(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE autogen_llm_configs (name TEXT, api_type TEXT, api_version TEXT, model TEXT, api_key TEXT, base_url TEXT)
    '''
    name: str = Field(..., description="LLM Configの名前")
    api_type: str = Field(..., description="LLMのAPIタイプ (例: openai, azure)")
    api_version: str = Field(..., description="LLMのAPIバージョン (例: 2023-05-15)")
    model: str = Field(..., description="LLMのモデル名 (例: gpt-3.5-turbo)")
    api_key: str = Field(..., description="LLMのAPIキー")   
    # Optionai
    base_url: Optional[str] = Field(None, description="LLMのベースURL (例: https://api.openai.com/v1)")

    @classmethod
    async def get_autogen_llm_config_list_api(cls):
        llm_config_list = await cls.get_autogen_llm_config_list()
        if not llm_config_list:
            raise ValueError("llm_config_list is not set")
        result = {}
        result["llm_config_list"] = [config.to_dict() for config in llm_config_list]
        return result

    @classmethod
    async def get_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogenLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        llm_config_result = await cls.get_autogen_llm_config(llm_config.name)
        result: dict = {}
        if llm_config_result:
            result["llm_config"] = llm_config_result.to_dict()
        return result

    @classmethod
    async def update_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogenLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        await cls.update_autogen_llm_config(llm_config)
        result: dict = {}
        return result

    @classmethod
    async def delete_autogen_llm_config_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        llm_config = AutogenLLMConfig.get_autogen_llm_config_object(request_dict)
        if not llm_config:
            raise ValueError("llm_config is not set")
        await cls.delete_autogen_llm_config(llm_config)
        result: dict = {}
        return result

    autogen_llm_config_request_name: ClassVar[str] = "autogen_llm_config_request"

    @classmethod
    def get_autogen_llm_config_object(cls, request_dict: dict) -> "AutogenLLMConfig":
        request: Optional[dict] = request_dict.get(cls.autogen_llm_config_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return AutogenLLMConfig(**request)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    async def get_autogen_llm_config_list(cls) -> List["AutogenLLMConfig"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_llm_configs")
                rows = await cur.fetchall()
                llm_configs = [AutogenLLMConfig(**dict(row)) for row in rows]

        return llm_configs
    
    @classmethod
    async def get_autogen_llm_config(cls, llm_config_name: str) -> Union["AutogenLLMConfig", None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM autogen_llm_configs WHERE name=?", (llm_config_name,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                llm_config_dict = dict(row)

        return AutogenLLMConfig(**llm_config_dict)
    
    @classmethod
    async def update_autogen_llm_config(cls, llm_config: "AutogenLLMConfig"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            cur = await conn.cursor()
            if await cls.get_autogen_llm_config(llm_config.name) is None:
                await cur.execute("INSERT INTO autogen_llm_configs VALUES (?, ?, ?, ?, ?, ?)", (llm_config.name, llm_config.api_type, llm_config.api_version, llm_config.model, llm_config.api_key, llm_config.base_url))
            else:
                await cur.execute("UPDATE autogen_llm_configs SET api_type=?, api_version=?, model=?, api_key=?, base_url=? WHERE name=?", (llm_config.api_type, llm_config.api_version, llm_config.model, llm_config.api_key, llm_config.base_url, llm_config.name))
            await conn.commit()
 
    @classmethod
    async def delete_autogen_llm_config(cls, llm_config: "AutogenLLMConfig"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM autogen_llm_configs WHERE name=?", (llm_config.name,))
                await conn.commit()

    @classmethod
    async def init_autogen_llm_config_table(cls):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    CREATE TABLE IF NOT EXISTS autogen_llm_configs (
                        name TEXT PRIMARY KEY,
                        api_type TEXT,
                        api_version TEXT,
                        model TEXT,
                        api_key TEXT,
                        base_url TEXT
                    )
                ''')
                await conn.commit()

        # テーブルの初期化
        await cls.__init_default_autogen_llm_config()

    @classmethod
    async def __init_default_autogen_llm_config(cls):
        # name="default"のAutogentLLMConfigを取得
        autogen_llm_config = cls.get_autogen_llm_config("default")
        # 存在しない場合は初期化処理
        if not autogen_llm_config:
            from ai_chat_lib.llm_modules.openai_util import OpenAIProps
            openai_props = OpenAIProps.create_from_env()
            if not openai_props:
                raise ValueError("OpenAI API key is not set in environment variables.")
            # OpenAIPropsからAPIキーを取得
            api_key = openai_props.openai_key
            if openai_props.azure_openai:
                api_type = "azure"
            else:
                api_type = "openai"
            # Azure OpenAIの場合はAPIバージョンを取得
            if openai_props.azure_openai:
                api_version = openai_props.azure_openai_api_version
                base_url = openai_props.azure_openai_endpoint
            else:
                api_version = ""
                base_url = openai_props.openai_base_url

            model = openai_props.default_completion_model

            # AutogentLLMConfigを作成
            params = {
                "name": "default",
                "api_type": api_type,
                "api_version": api_version,
                "model": model,
                "api_key": api_key,
                "base_url": base_url
            }
            autogen_llm_config = AutogenLLMConfig(**params)
            # MainDBに追加
            await cls.update_autogen_llm_config(autogen_llm_config)
        else:
            # 存在する場合は初期化処理を行わない
            logger.info("AutogentLLMConfig is already exists.")
