"""
content_item.py

ContentItemsテーブルのデータモデルおよび関連DB操作・APIユーティリティを提供するモジュール。
"""

import aiosqlite
from typing import List, Union, Optional, ClassVar, Sequence
from pydantic import BaseModel, field_validator, Field

import ai_chat_lib.model as model_base

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.vector_db_item import MainDB
from ai_chat_lib.db_modules.search_condition import SearchCondition

class ContentItem(model_base.ContentItemModel):

    """
    ContentItemsテーブルの1レコードを表現するデータモデルクラス。
    DBとのマッピング、APIリクエスト/レスポンス変換、各種DB操作ユーティリティを提供する。

    テーブル定義:
    CREATE TABLE "ContentItems" (
        "id" TEXT NOT NULL CONSTRAINT "PK_ContentItems" PRIMARY KEY,
        "folder_id" TEXT NULL,
        "created_at" TEXT NOT NULL,
        "updated_at" TEXT NOT NULL,
        "vectorized_at" TEXT NOT NULL,
        "content" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "content_type" INTEGER NOT NULL,
        "chat_messages_json" TEXT NOT NULL,
        "prompt_chat_result_json" TEXT NOT NULL,
        "tag_string" TEXT NOT NULL,
        "is_pinned" INTEGER NOT NULL,
        "cached_base64_string" TEXT NOT NULL,
        "extended_properties_json" TEXT NOT NULL
    )
    """

    @classmethod
    async def create_table(cls):
        """
        ContentItemsテーブルをDBに作成する（存在しない場合のみ）。
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS "ContentItems" (
                    "id" TEXT NOT NULL CONSTRAINT "PK_ContentItems" PRIMARY KEY,
                    "folder_id" TEXT NULL,
                    "created_at" TEXT NOT NULL,
                    "updated_at" TEXT NOT NULL,
                    "vectorized_at" TEXT NOT NULL,
                    "content" TEXT NOT NULL,
                    "description" TEXT NOT NULL,
                    "content_type" INTEGER NOT NULL,
                    "chat_messages_json" TEXT NOT NULL,
                    "prompt_chat_result_json" TEXT NOT NULL,
                    "tag_string" TEXT NOT NULL,
                    "is_pinned" INTEGER NOT NULL,
                    "cached_base64_string" TEXT NOT NULL,
                    "extended_properties_json" TEXT NOT NULL
                )
            ''')
            await conn.commit()

    @classmethod
    async def update_default_data(cls):
        """
        ContentItemsテーブルのfolder_idにインデックスを追加する。
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_folder_id ON ContentItems (folder_id)
            ''')
            await conn.commit()


    @classmethod
    async def get_content_items_by_folder_id(cls, folder_id: str) -> List["ContentItem"]:
        """
        指定フォルダIDに紐づくContentItem一覧を取得する。

        Args:
            folder_id (str): フォルダID

        Returns:
            List[ContentItem]: 該当するContentItemのリスト
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems WHERE folder_id = ?", (folder_id,))
                rows = await cur.fetchall()
                content_items = [ContentItem(**dict(row)) for row in rows]
                return content_items    

    @classmethod
    async def get_content_items(cls) -> List["ContentItem"]:
        """
        全ContentItemを取得する。

        Returns:
            List[ContentItem]: 全ContentItemのリスト
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems")
                rows = await cur.fetchall()
                content_items = [ContentItem(**dict(row)) for row in rows]
                return content_items

    @classmethod
    async def get_content_item_by_id(cls, item_id: str) -> Optional["ContentItem"]:
        """
        指定IDのContentItemを取得する。

        Args:
            item_id (str): ContentItemのID

        Returns:
            Optional[ContentItem]: 該当するContentItem、存在しない場合はNone
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentItems WHERE id = ?", (item_id,))
                row = await cur.fetchone()
                if row:
                    return ContentItem(**dict(row))
                return None
    
    @classmethod
    async def update_content_item(cls, item: model_base.ContentItemModel) -> model_base.ContentItemModel:
        """
        ContentItemを新規追加または更新する。

        Args:
            item (model_base.ContentItemModel): 追加・更新対象のContentItem

        Returns:
            model_base.ContentItemModel: 追加・更新後のContentItem
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                if await cls.get_content_item_by_id(item.id) is None:
                    # 新規追加
                    await cur.execute('''
                        INSERT INTO ContentItems (
                            id, folder_id, created_at, updated_at, vectorized_at,
                            content, description, content_type, chat_messages_json,
                            prompt_chat_result_json, tag_string, is_pinned,
                            cached_base64_string, extended_properties_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.id, item.folder_id, item.created_at, item.updated_at,
                        item.vectorized_at, item.content, item.description,
                        item.content_type, item.chat_messages_json,
                        item.prompt_chat_result_json, item.tag_string,
                        item.is_pinned, item.cached_base64_string,
                        item.extended_properties_json
                    ))
                else:
                    # 更新
                    await cur.execute('''
                        UPDATE ContentItems SET
                            folder_id = ?, updated_at = ?, vectorized_at = ?,
                            content = ?, description = ?, content_type = ?,
                            chat_messages_json = ?, prompt_chat_result_json = ?,
                            tag_string = ?, is_pinned = ?,
                            cached_base64_string = ?, extended_properties_json = ?
                        WHERE id = ?
                    ''', (
                        item.folder_id, item.updated_at, item.vectorized_at,
                        item.content, item.description, item.content_type,
                        item.chat_messages_json, item.prompt_chat_result_json,
                        item.tag_string, item.is_pinned,
                        item.cached_base64_string, item.extended_properties_json,
                        item.id
                    ))
                await conn.commit()
        return item

    @classmethod
    async def delete_content_item(cls, item: model_base.ContentItemModel) -> None:
        """
        指定ContentItemを削除する。

        Args:
            item (model_base.ContentItemModel): 削除対象
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM ContentItems WHERE id = ?", (item.id,))
                await conn.commit()
        logger.info(f"ContentItem with id {item.id} deleted.")

    @classmethod
    async def delete_content_items(cls, items: Sequence[model_base.ContentItemModel]) -> None:
        """
        指定ContentItem群を削除する。

        Args:
            items (Sequence[model_base.ContentItemModel]): 削除対象群
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.executemany("DELETE FROM ContentItems WHERE id = ?", [(item.id,) for item in items])
                await conn.commit()
        logger.info(f"ContentItems with ids {[item.id for item in items]} deleted.")

    @classmethod
    async def search_content_items(cls, search_condition: SearchCondition) -> List["ContentItem"]:
        """
        検索条件に基づいてContentItemを検索する。

        Args:
            search_condition (SearchCondition): 検索条件

        Returns:
            List[ContentItem]: 検索結果のContentItemリスト
        """
        query = "SELECT * FROM ContentItems WHERE 1=1"
        params = []

        if search_condition.description and not search_condition.exclude_description:
            query += " AND description LIKE ?"
            params.append(f"%{search_condition.description}%")
        
        if search_condition.content and not search_condition.exclude_content:
            query += " AND content LIKE ?"
            params.append(f"%{search_condition.content}%")
        
        if search_condition.tags and not search_condition.exclude_tags:
            query += " AND tag_string LIKE ?"
            params.append(f"%{search_condition.tags}%")
        
        if search_condition.source_application_name and not search_condition.exclude_source_application_name:
            query += " AND source_application_name LIKE ?"
            params.append(f"%{search_condition.source_application_name}%")
        
        if search_condition.source_application_title and not search_condition.exclude_source_application_title:
            query += " AND source_application_title LIKE ?"
            params.append(f"%{search_condition.source_application_title}%")
        
        if search_condition.enable_start_time and search_condition.start_time_str:
            query += " AND created_at >= ?"
            params.append(search_condition.start_time_str)
        
        if search_condition.enable_end_time and search_condition.end_time_str:
            query += " AND created_at <= ?"
            params.append(search_condition.end_time_str)

        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                params_str = query + "".join(params)
                logger.debug(f"Executing search query: {params_str}")

                await cur.execute(query, tuple(params))
                rows = await cur.fetchall()
                return [ContentItem(**dict(row)) for row in rows]

    @classmethod
    async def delete_content_items_by_folder_id(cls, folder_id: str) -> None:
        """
        指定フォルダID配下のContentItemを全削除する。

        Args:
            folder_id (str): フォルダID
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM ContentItems WHERE folder_id = ?", (folder_id,))
                await conn.commit()
        logger.info(f"ContentItems in folder {folder_id} deleted.")

    def to_dict(self) -> dict:
        """
        ContentItemをdict形式に変換する。

        Returns:
            dict: ContentItemの辞書表現
        """
        return self.model_dump()

    
    @classmethod
    async def update_content_items(cls, content_items: Sequence[model_base.ContentItemModel]) -> Sequence[model_base.ContentItemModel]:
        """
        ContentItemの追加・更新をAPIリクエスト形式で受け付けて実行する。

        Args:
            content_items (Sequence[model_base.ContentItemModel]): 更新対象のContentItemリスト
        Returns:
            Sequence[model_base.ContentItemModel]: 更新結果
        Raises:
            ValueError: リクエスト不備時
        """
        if not content_items:
            raise ValueError("No valid content items found in the request.")
        
        updated_items = []
        for item in content_items:
            updated_item = await ContentItem.update_content_item(item)
            updated_items.append(updated_item)

        return updated_items
