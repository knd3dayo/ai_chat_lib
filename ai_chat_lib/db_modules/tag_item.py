from typing import List, Union, Sequence
import aiosqlite

import ai_chat_lib.model as model_base

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.main_db import MainDB

class TagItem(model_base.TagItemModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "TagItems" (
    "id" TEXT NOT NULL CONSTRAINT "PK_TagItems" PRIMARY KEY,
    "tag" TEXT NOT NULL,
    "is_pinned" INTEGER NOT NULL
    )
    '''

    @classmethod
    async def get_tag_item(cls, tag_id: str) -> Union[model_base.TagItemModel, None]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM TagItems WHERE id=?", (tag_id,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                tag_item_dict = dict(row)

        return TagItem(**tag_item_dict)
    
    @classmethod
    async def get_tag_items(cls) -> Sequence[model_base.TagItemModel]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM TagItems")
                rows = await cur.fetchall()
                tag_items = [TagItem(**dict(row)) for row in rows]

        return tag_items
    
    @classmethod
    async def update_tag_item(cls, tag_item: model_base.TagItemModel) -> model_base.TagItemModel:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                if await cls.get_tag_item(tag_item.id) is None:
                    await cur.execute("INSERT INTO TagItems VALUES (?, ?, ?)", (tag_item.id, tag_item.tag, tag_item.is_pinned))
                else:
                    await cur.execute("UPDATE TagItems SET tag=?, is_pinned=? WHERE id=?", (tag_item.tag, tag_item.is_pinned, tag_item.id))
                await conn.commit()

        # 更新したTagItemを返す
        return tag_item
    
    @classmethod
    async def update_tag_items(cls, tag_items: Sequence[model_base.TagItemModel]) -> Sequence[model_base.TagItemModel]:
        updated_items = []
        for tag_item in tag_items:
            updated_item = await cls.update_tag_item(tag_item)
            updated_items.append(updated_item)
        return updated_items
    
    @classmethod
    async def delete_tag_item(cls, tag_item: model_base.TagItemModel):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM TagItems WHERE id=?", (tag_item.id,))
                await conn.commit()
    
    @classmethod
    async def delete_tag_items(cls, tag_items: Sequence[model_base.TagItemModel]) -> None:
        for tag_item in tag_items:
            await cls.delete_tag_item(tag_item)

    @classmethod
    async def create_table(cls):
        # TagItemsテーブルが存在しない場合は作成する
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                # テーブルが存在するか確認
                row = await cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TagItems'")
                table = await row.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("TagItems table already exists.")
                    return
                else:
                    # テーブルが存在しない場合は作成する
                    logger.debug("Creating TagItems table.")

                    await cur.execute('''
                        CREATE TABLE IF NOT EXISTS TagItems (
                            id TEXT NOT NULL PRIMARY KEY,
                            tag TEXT NOT NULL,
                            is_pinned INTEGER NOT NULL
                        )
                    ''')
                    await conn.commit()
