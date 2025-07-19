"""
main_db_util.py

メインDBの初期化・アップグレード・テーブル作成など、DB管理のユーティリティクラスを提供するモジュール。
"""

import os
import sqlite3
from typing import Union
import ai_chat_lib.log_modules.log_settings as log_settings
from ai_chat_lib.db_modules.main_db import MainDB
from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.db_modules.content_item import ContentItem
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
    """
    メインDBの初期化・アップグレード・テーブル作成などを行うユーティリティクラス。
    """

    @classmethod
    async def init(cls, upgrade: bool = False):
        """
        メインDBの初期化処理を実行する。

        Args:
            upgrade (bool): Trueの場合はDBのアップグレードも実施する
        """
        # main_dbへのパスを取得
        app_db_path = MainDB.get_main_db_path()
        await cls.__init_database(app_db_path, upgrade)

    @classmethod
    async def __init_database(cls, app_db_path: str, upgrade: bool = False):
        """
        指定パスにDBファイルがなければ作成し、テーブル初期化・アップグレードを行う。

        Args:
            app_db_path (str): DBファイルのパス
            upgrade (bool): Trueの場合はDBのアップグレードも実施する
        """
        # db_pathが存在しない場合は作成する
        if not os.path.exists(app_db_path):
            os.makedirs(os.path.dirname(app_db_path), exist_ok=True)

        # 空のDBファイルを作成
        conn = sqlite3.connect(app_db_path)
        conn.close()

        # テーブルの初期化
        await cls.__init_tables()

        if upgrade:
            # DBのアップグレード処理
            cls.__update_database()

    @classmethod
    def __update_database(cls):
        """
        DBのアップグレード処理（未実装）
        """
        # TODO: 必要に応じてDBスキーマのアップグレード処理を実装
        pass

    @classmethod
    async def __init_tables(cls):
        """
        必要な全テーブルの初期化（作成）を行う。
        """
        # DBPropertiesテーブルを初期化
        await MainDB.create_table()
        # ContentFoldersテーブルを初期化
        await ContentFolder.create_table()
        # ContentItemテーブルを初期化
        await ContentItem.create_table()
        # PromptItemsテーブルを初期化
        await PromptItem.create_table()
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
