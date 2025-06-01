
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



logger = log_settings.getLogger(__name__)


class MainDBUtil:

    @classmethod
    def init(cls, upgrade: bool = False):
        # main_dbへのパスを取得
        app_db_path = MainDB.get_main_db_path()
        cls.__init_database(app_db_path, upgrade)

    @classmethod
    def __init_database(cls, app_db_path: str, upgrade: bool = False):

        # db_pathが存在しない場合は作成する
        if not os.path.exists(app_db_path):
            os.makedirs(os.path.dirname(app_db_path), exist_ok=True)
            conn = sqlite3.connect(app_db_path)
            conn.close()
            # テーブルの初期化
            cls.__init_tables()

        if upgrade:
            # DBのアップグレード処理
            cls.__update_database()

    @classmethod
    def __update_database(cls):
        # DBのアップグレード処理
        pass

    @classmethod
    def __init_tables(cls):
        # DBPropertiesテーブルを初期化
        MainDB.init_db_properties_table()
        # ContentFoldersテーブルを初期化
        ContentFoldersCatalog.init_content_folder_catalog_table()
        # TagItemsテーブルを初期化
        TagItem.init_tag_item_table()
        # VectorDBItemsテーブルを初期化
        VectorDBItem.init_vector_db_item_table()
        # autogen_llm_configsテーブルを初期化
        AutogenLLMConfig.init_autogen_llm_config_table()

        # autogen_toolsテーブルを初期化
        AutogenTools.init_autogen_tools_table()
        # autogen_agentsテーブルを初期化
        AutogenAgent.init_autogen_agents_table()
        # autogen_group_chatsテーブルを初期化
        AutogenGroupChat.init_autogen_group_chats_table()
