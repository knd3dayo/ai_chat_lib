from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
import json
import uuid
from ai_chat_lib.resouces import *
from ai_chat_lib.db_modules.main_db import MainDB

class PromptItem(BaseModel):
    """
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "PromptItems" (
	"id"	TEXT NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"prompt"	TEXT NOT NULL,
	"prompt_template_type"	INTEGER NOT NULL,
	"extended_properties_json"	TEXT NOT NULL,
	PRIMARY KEY("id")
    )
    prompt_template_typeの値は以下のように定義される
    - 0: System Defined Prompt
    - 1: Modified System Defined Prompt
    - 2: User Defined Prompt
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the prompt item")
    name: str = Field(..., description="Name of the prompt item")
    description: str = Field(..., description="Description of the prompt item")
    prompt: str = Field(..., description="The prompt text")
    prompt_template_type: int = Field(..., description="Type of the prompt template")
    extended_properties_json: str = Field(..., description="JSON string of extended properties")

    get_prompt_item_requests_name: ClassVar[str] = "prompt_item_requests"

    @classmethod
    async def create_table(cls):
        # ContentFoldersテーブルが存在しない場合は作成する
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    CREATE TABLE IF NOT EXISTS PromptItems (
                        id TEXT NOT NULL PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        prompt TEXT NOT NULL,
                        prompt_template_type INTEGER NOT NULL,
                        extended_properties_json TEXT NOT NULL
                    )
                ''')
                await conn.commit()

        # 初期のPromptItemsを設定する
        await cls.update_default_data()

    @classmethod
    async def update_default_data(cls):
        """
        初期のPromptItemsを設定する
        """
        resources = resource_util.get_string_resources()
        title_generation = await cls.get_system_defined_prompt_by_name("TitleGeneration")
        if title_generation is None:
            title_generation_id = str(uuid.uuid4())
        else:
            title_generation_id = title_generation.id

        title_generation =  {
            "id": title_generation_id,
            "name": "TitleGeneration",
            "description": resources.prompt_item_tile_generation,
            "prompt": resources.prompt_item_tile_generation_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": True, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 2, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        background_information_generation = await cls.get_system_defined_prompt_by_name("BackgroundInformationGeneration")
        if background_information_generation is None:
            background_information_generation_id = str(uuid.uuid4())
        else:
            background_information_generation_id = background_information_generation.id

        background_information_generation = {
            "id": background_information_generation_id,
            "name": "BackgroundInformationGeneration",
            "description": resources.prompt_item_background_information_generation,
            "prompt": resources.prompt_item_background_information_generation_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 1, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }

        summary_generation = await cls.get_system_defined_prompt_by_name("SummaryGeneration")
        if summary_generation is None:
            summary_generation_id = str(uuid.uuid4())
        else:
            summary_generation_id = summary_generation.id
        summary_generation =  {
            "id": summary_generation_id,                
            "name": "SummaryGeneration",
            "description": resources.prompt_item_summary_generation,
            "prompt": resources.prompt_item_summary_generation_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        tasks_generation = await cls.get_system_defined_prompt_by_name("TasksGeneration")
        if tasks_generation is None:
            tasks_generation_id = str(uuid.uuid4())
        else:
            tasks_generation_id = tasks_generation.id
        tasks_generation = {
            "id": tasks_generation_id,
            "name": "TasksGeneration",
            "description": resources.prompt_item_task_generation,
            "prompt": resources.prompt_item_task_generation_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 2, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }

        # DocumentReliabilityCheck
        document_reliability_check = await cls.get_system_defined_prompt_by_name("DocumentReliabilityCheck")
        if document_reliability_check is None:
            document_reliability_check_id = str(uuid.uuid4())
        else:
            document_reliability_check_id = document_reliability_check.id
        document_reliability_check = {
            "id": document_reliability_check_id,
            "name": "DocumentReliabilityCheck",
            "description": resources.prompt_item_document_relaiability_check,
            "prompt": resources.prompt_item_document_relaiability_check_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        # TagGeneration
        tag_generation = await cls.get_system_defined_prompt_by_name("TagGeneration")
        if tag_generation is None:
            tag_generation_id = str(uuid.uuid4())
        else:
            tag_generation_id = tag_generation.id
        tag_generation = {
            "id": tag_generation_id,
            "name": "TagGeneration",
            "description": resources.prompt_item_tag_generation,
            "prompt": resources.prompt_item_tag_generation_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 1, # 0: TextContent, 1: ListContent, 2: TableContent 
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 3, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        # SelectExistingTags
        select_existing_tags = await cls.get_system_defined_prompt_by_name("SelectExistingTags")
        if select_existing_tags is None:
            select_existing_tags_id = str(uuid.uuid4())
        else:
            select_existing_tags_id = select_existing_tags.id
        select_existing_tags = {
            "id": select_existing_tags_id,
            "name": "SelectExistingTags",
            "description": resources.prompt_item_select_existing_tags,
            "prompt": resources.prompt_item_select_existing_tags_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 1, # 0: TextContent, 1: ListContent, 2: TableContent 
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": True, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 3, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        # prompt_item_clipboard_intent
        clipboard_intent = await cls.get_system_defined_prompt_by_name("ClipboardIntent")
        if clipboard_intent is None:
            clipboard_intent_id = str(uuid.uuid4())
        else:
            clipboard_intent_id = clipboard_intent.id
        clipboard_intent = {
            "id": clipboard_intent_id,
            "name": "PredictUserIntentFromClipboard",
            "description": resources.prompt_item_clipboard_intent,
            "prompt": resources.prompt_item_clipboard_intent_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent 
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        # prompt_item_screen_intent
        screen_intent = await cls.get_system_defined_prompt_by_name("ScreenIntent")
        if screen_intent is None:
            screen_intent_id = str(uuid.uuid4())
        else:
            screen_intent_id = screen_intent.id
        screen_intent = {
            "id": screen_intent_id,
            "name": "PredictUserIntentFromImage",
            "description": resources.prompt_item_screen_intent,
            "prompt": resources.prompt_item_screen_intent_prompt,
            "prompt_template_type": 0, # 0: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent 
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }

        # PromptItemsテーブルにデータを挿入する
        for item in [
            title_generation,
            background_information_generation,
            summary_generation,
            tasks_generation,
            document_reliability_check,
            tag_generation,
            select_existing_tags,
            clipboard_intent,
            screen_intent
        ]:
            prompt_item = PromptItem(**item)
            await cls.update_prompt_item(prompt_item)


    @classmethod
    def get_prompt_item_objects(cls, request_dict: dict) -> list["PromptItem"]:
        '''
        {"prompt_ttem_requests": [] }の形式で渡される
        '''
        prompt_items = request_dict.get(cls.get_prompt_item_requests_name, None)
        if not prompt_items:
            raise ValueError("prompt_items is not set.")
        return [cls(**item) for item in prompt_items]


    @classmethod
    async def get_prommt_items_api(cls) -> dict:
        """
        PromptItemsテーブルから全てのデータを取得し、API用の辞書形式で返す
        """
        prompt_items = await cls.get_prompt_items()
        return {
            "prompt_items": [item.model_dump() for item in prompt_items],
        }
    
    @classmethod
    async def get_prompt_item_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを取得し、API用の辞書形式で返す
        """
        request_dict: dict = json.loads(request_json)
        id: Union[str, None] = cls.get_prompt_item_objects(request_dict)[0].id if cls.get_prompt_item_objects(request_dict) else None
        if id is None:
            raise ValueError("id is not set in the request.")
        prompt_item = await cls.get_prompt_item_by_id(id)
        if prompt_item is None:
            return {"prompt_item": None}
        return{
            "prompt_item": prompt_item.model_dump()
        }
    
    @classmethod
    async def update_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルのデータを更新する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = cls.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            prompt_item = cls(**prompt_item_data.model_dump())
            await cls.update_prompt_item(prompt_item)
    
        return {}
    
    @classmethod
    async def delete_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを削除する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = cls.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            await cls.delete_prompt_item(prompt_item_data.id)
    
        return {}

    @classmethod
    async def get_prompt_items(cls) -> list["PromptItem"]:
        """
        PromptItemsテーブルから全てのデータを取得する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM PromptItems")
                rows = await cur.fetchall()
                prompt_items = [PromptItem(**dict(row)) for row in rows]
        return prompt_items

    @classmethod
    async def get_prompt_item_by_id(cls, id: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定されたIDのデータを取得する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM PromptItems WHERE id=?", (id,))
                row = await cur.fetchone()
                if row is None:
                    return None

                return PromptItem(**dict(row))


    @classmethod
    async def get_system_defined_prompt_by_name(cls, name: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された名前のシステム定義プロンプトを取得する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM PromptItems WHERE name=? AND prompt_template_type=1", (name,))
                row = await cur.fetchone()
                if row is None:
                    return None

                return PromptItem(**dict(row))

    @classmethod
    async def get_prompt_item_by_name(cls, name: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された名前のデータを取得する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM PromptItems WHERE name=?", (name,))
                row = await cur.fetchone()
                if row is None:
                    return None

                return PromptItem(**dict(row))
    
    @classmethod
    async def get_prompt_item_by_description(cls, description: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された説明のデータを取得する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM PromptItems WHERE description=?", (description,))
                row = await cur.fetchone()
                if row is None:
                    return None
                
                return PromptItem(**dict(row))
    
    @classmethod
    async def update_prompt_item(cls, prompt_item: "PromptItem") -> None:
        """
        PromptItemsテーブルのデータを更新する
        idに一致したデータを更新する
        一致したデータが存在しない場合はinsertする
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                item = await cls.get_prompt_item_by_id(prompt_item.id)
                if item is None:
                    # データが存在しない場合はinsertする
                    await cur.execute('''
                        INSERT INTO PromptItems (id, name, description, prompt, prompt_template_type, extended_properties_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (prompt_item.id, prompt_item.name, prompt_item.description, prompt_item.prompt,
                          prompt_item.prompt_template_type, prompt_item.extended_properties_json))
                else:
                    # データが存在する場合はupdateする
                    await cur.execute('''
                        UPDATE PromptItems SET name=?, description=?, prompt=?, prompt_template_type=?, extended_properties_json=?
                        WHERE id=?
                    ''', (prompt_item.name, prompt_item.description, prompt_item.prompt,
                          prompt_item.prompt_template_type, prompt_item.extended_properties_json, prompt_item.id))
                await conn.commit()

    @classmethod
    async def delete_prompt_item(cls, id: str) -> None:
        """
        PromptItemsテーブルから指定されたIDのデータを削除する
        """
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM PromptItems WHERE id=?", (id,))
                await conn.commit()
