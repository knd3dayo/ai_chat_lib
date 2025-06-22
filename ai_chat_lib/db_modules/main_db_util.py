
import os
import sqlite3
from typing import Union
import ai_chat_lib.log_modules.log_settings as log_settings
from ai_chat_lib.db_modules.main_db import MainDB
from ai_chat_lib.db_modules.content_folders_catalog import ContentFoldersCatalog
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from ai_chat_lib.db_modules.tag_item import TagItem
from ai_chat_lib.db_modules.autogen_llm_config import AutogenLLMConfig
from ai_chat_lib.db_modules.autogen_tools import AutogenTools
from ai_chat_lib.db_modules.autogen_agent import AutogenAgent
from ai_chat_lib.db_modules.autogen_group_chat import AutogenGroupChat
from ai_chat_lib.db_modules.prompt_item import PromptItem
from ai_chat_lib.db_modules.auto_process_item import AutoProcessItem
from ai_chat_lib.db_modules.auto_process_rule import AutoProcessRule
from ai_chat_lib.db_modules.search_rule import SearchRule

logger = log_settings.getLogger(__name__)


class MainDBUtil:

    @classmethod
    async def init(cls, upgrade: bool = False, update_default_data: bool = False):
        # main_dbへのパスを取得
        app_db_path = MainDB.get_main_db_path()
        await cls.__init_database(app_db_path,  upgrade, update_default_data)

    @classmethod
    async def __init_database(cls, app_db_path: str, upgrade: bool = False, update_default_data: bool = False):

        # db_pathが存在しない場合は作成する
        if not os.path.exists(app_db_path):
            os.makedirs(os.path.dirname(app_db_path), exist_ok=True)
            conn = sqlite3.connect(app_db_path)
            conn.close()
            # テーブルの初期化
            await cls.__init_tables()

        if upgrade:
            # DBのアップグレード処理
            cls.__update_database()

        if update_default_data:
            # デフォルトデータの更新処理
            await cls.__update_default_data()

    @classmethod
    def __update_database(cls):
        # DBのアップグレード処理
        pass

    @classmethod
    async def __init_tables(cls):
        # DBPropertiesテーブルを初期化
        await MainDB.create_table()
        # ContentFoldersテーブルを初期化
        await ContentFoldersCatalog.create_table()
        # PromptItemsテーブルを初期化
        await PromptItem.create_table()
        # TagItemsテーブルを初期化
        # AutoProcessItemテーブルを初期化
        await AutoProcessItem.create_table()
        # AutoProcessRuleテーブルを初期化
        await AutoProcessRule.create_table()
        # SearchRuleテーブルを初期化
        await SearchRule.create_table()
        # TagItemテーブルを初期化
        await TagItem.create_table()
        # VectorDBItemsテーブルを初期化
        await VectorDBItem.create_table()
        # autogen_llm_configsテーブルを初期化
        await AutogenLLMConfig.create_table()
        # autogen_toolsテーブルを初期化
        await AutogenTools.create_table()
        # autogen_agentsテーブルを初期化
        await AutogenAgent.create_table()
        # autogen_group_chatsテーブルを初期化
        await AutogenGroupChat.create_table()

    @classmethod
    async def __update_default_data(cls):
        # DBPropertiesテーブルを初期化
        # await MainDB.update_default_data()
        # ContentFoldersテーブルを初期化
        await ContentFoldersCatalog.update_default_data()
        # PromptItemsテーブルを初期化
        await PromptItem.update_default_data()
        # TagItemsテーブルを初期化
        # AutoProcessItemテーブルを初期化
        await AutoProcessItem.update_default_data()
        # AutoProcessRuleテーブルを初期化
        # await AutoProcessRule.update_default_data()
        # SearchRuleテーブルを初期化
        # await SearchRule.update_default_data()
        # TagItemテーブルを初期化
         #await TagItem.update_default_data()
        # VectorDBItemsテーブルを初期化
        await VectorDBItem.update_default_data()
        # autogen_llm_configsテーブルを初期化
        await AutogenLLMConfig.update_default_data()
        # autogen_toolsテーブルを初期化
        await AutogenTools.update_default_data()
        # autogen_agentsテーブルを初期化
        await AutogenAgent.update_default_data()
        # autogen_group_chatsテーブルを初期化
        await AutogenGroupChat.update_default_data()
