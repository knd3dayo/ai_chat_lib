from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import sqlite3
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
    """
    id: str = Field(..., description="Unique identifier for the prompt item")
    name: str = Field(..., description="Name of the prompt item")
    description: str = Field(..., description="Description of the prompt item")
    prompt: str = Field(..., description="The prompt text")
    prompt_template_type: int = Field(..., description="Type of the prompt template")
    extended_properties_json: str = Field(..., description="JSON string of extended properties")

    get_prompt_item_requests_name: ClassVar[str] = "prompt_item_requests"

    @classmethod
    def init_prompt_item_table(cls):
        # ContentFoldersテーブルが存在しない場合は作成する
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS PromptItems (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                prompt TEXT NOT NULL,
                prompt_template_type INTEGER NOT NULL,
                extended_properties_json TEXT NOT NULL
            )
        ''')

        conn.commit()
        conn.close()
        # 初期のPromptItemsを設定する
        cls.__init_default_prompt_items()

    @classmethod
    def __init_default_prompt_items(cls):
        """
        初期のPromptItemsを設定する
        """
        resources = resource_util.get_string_resources()
        title_generation_id = cls.get_system_defined_prompt_by_name("TitleGeneration")
        if title_generation_id is None:
            title_generation_id = str(uuid.uuid4())

        title_generation =  {
            "id": title_generation_id,
            "name": "TitleGeneration",
            "description": resources.prompt_item_tile_generation,
            "prompt": resources.prompt_item_tile_generation,
            "prompt_template_type": 1, # 1: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": True, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 2, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        background_information_generation_id = cls.get_system_defined_prompt_by_name("BackgroundInformationGeneration")
        if background_information_generation_id is None:
            background_information_generation_id = str(uuid.uuid4())

        background_information_generation = {
            "id": background_information_generation_id,
            "name": "BackgroundInformationGeneration",
            "description": resources.prompt_item_background_information_generation,
            "prompt": resources.prompt_item_background_information_generation_prompt,
            "prompt_template_type": 1, # 1: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 1, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }

        summary_generation_id = cls.get_system_defined_prompt_by_name("SummaryGeneration")
        if summary_generation_id is None:
            summary_generation_id = str(uuid.uuid4())
        summary_generation =  {
            "id": summary_generation_id,                
            "name": "SummaryGeneration",
            "description": resources.prompt_item_summary_generation,
            "prompt": resources.prompt_item_summary_generation_prompt,
            "prompt_template_type": 1, # 1: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 0, # 0: TextContent, 1: ListContent, 2: TableContent
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 2, # 0: No Split, 1: Split Only, 2: Split and Summarize 
                "use_taglist": False, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 0, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
            }, ensure_ascii=False, indent=4)
        }
        tasks_generation_id = cls.get_system_defined_prompt_by_name("TasksGeneration")
        if tasks_generation_id is None:
            tasks_generation_id = str(uuid.uuid4())
        tasks_generation = {
            "id": tasks_generation_id,
                "name": "TasksGeneration",
                "description": resources.prompt_item_task_generation,
                "prompt": resources.prompt_item_task_generation_prompt,
                "prompt_template_type": 1, # 1: System Defined Prompt
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
        document_reliability_check_id = cls.get_system_defined_prompt_by_name("DocumentReliabilityCheck")
        if document_reliability_check_id is None:
            document_reliability_check_id = str(uuid.uuid4())
        document_reliability_check = {
            "id": document_reliability_check_id,
            "name": "DocumentReliabilityCheck",
            "description": resources.prompt_item_document_relaiability_check,
            "prompt": resources.prompt_item_document_relaiability_check_prompt,
            "prompt_template_type": 1, # 1: System Defined Prompt
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
        tag_generation_id = cls.get_system_defined_prompt_by_name("TagGeneration")
        if tag_generation_id is None:
            tag_generation_id = str(uuid.uuid4())
        tag_generation = {
            "id": tag_generation_id,
            "name": "TagGeneration",
            "description": resources.prompt_item_tag_generation,
            "prompt": resources.prompt_item_tag_generation_prompt,
            "prompt_template_type": 1, # 1: System Defined Prompt
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
        select_existing_tags_id = cls.get_system_defined_prompt_by_name("SelectExistingTags")
        if select_existing_tags_id is None:
            select_existing_tags_id = str(uuid.uuid4())
        select_existing_tags = {
            "id": select_existing_tags_id,
            "name": "SelectExistingTags",
            "description": resources.prompt_item_select_existing_tags,
            "prompt": resources.prompt_item_select_existing_tags_prompt,
            "prompt_template_type": 1, # 1: System Defined Prompt
            "extended_properties_json": json.dumps({
                "prompt_result_type": 1, # 0: TextContent, 1: ListContent, 2: TableContent 
                "chat_mode": 0, # 0: Normal Chat 
                "split_mode": 0, # 0: No Split
                "use_taglist": True, # タグリストを使用するかどうか
                "rag_mode": 0, # 0: No RAG, 1: Normal RAG, 2: Prompt RAG
                "prompt_output_type": 3, # 0: new content, 1: overwrite content, 2: overwrite title, 3: append tag
                
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
            select_existing_tags
        ]:
            prompt_item = PromptItem(**item)
            cls.update_prompt_item(prompt_item)


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
    def get_prommt_items_api(cls) -> dict:
        """
        PromptItemsテーブルから全てのデータを取得し、API用の辞書形式で返す
        """
        prompt_items = cls.get_prompt_items()
        return {
            "prompt_items": [item.model_dump() for item in prompt_items],
        }
    
    @classmethod
    def get_prompt_item_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを取得し、API用の辞書形式で返す
        """
        request_dict: dict = json.loads(request_json)
        id: Union[str, None] = cls.get_prompt_item_objects(request_dict)[0].id if cls.get_prompt_item_objects(request_dict) else None
        if id is None:
            raise ValueError("id is not set in the request.")
        prompt_item = cls.get_prompt_item_by_id(id)
        if prompt_item is None:
            return {"prompt_item": None}
        return{
            "prompt_item": prompt_item.model_dump()
        }
    
    @classmethod
    def update_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルのデータを更新する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = cls.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            prompt_item = cls(**prompt_item_data.model_dump())
            cls.update_prompt_item(prompt_item)
    
        return {}
    
    @classmethod
    def delete_prompt_items_api(cls, request_json: str) -> dict:
        """
        PromptItemsテーブルから指定されたIDのデータを削除する
        """
        request_dict: dict = json.loads(request_json)
        prompt_items_data = cls.get_prompt_item_objects(request_dict)
        if not prompt_items_data:
            raise ValueError("prompt_items is not set in the request.")
        for prompt_item_data in prompt_items_data:
            cls.delete_prompt_item(prompt_item_data.id)
    
        return {}

    @classmethod
    def get_prompt_items(cls) -> list["PromptItem"]:
        """
        PromptItemsテーブルから全てのデータを取得する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM PromptItems")
        rows = cur.fetchall()
        conn.close()
        prompt_items = [PromptItem(**dict(row)) for row in rows]
        return prompt_items

    @classmethod
    def get_prompt_item_by_id(cls, id: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定されたIDのデータを取得する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM PromptItems WHERE id=?", (id,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return PromptItem(**dict(row))

    @classmethod
    def get_system_defined_prompt_by_name(cls, name: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された名前のシステム定義プロンプトを取得する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM PromptItems WHERE name=? AND prompt_template_type=1", (name,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return PromptItem(**dict(row))

    @classmethod
    def get_prompt_item_by_name(cls, name: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された名前のデータを取得する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM PromptItems WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return PromptItem(**dict(row))  
    
    @classmethod
    def get_prompt_item_by_description(cls, description: str) -> Optional["PromptItem"]:
        """
        PromptItemsテーブルから指定された説明のデータを取得する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM PromptItems WHERE description=?", (description,))
        row = cur.fetchone()
        conn.close()

        if row is None:
            return None

        return PromptItem(**dict(row))
    
    @classmethod
    def update_prompt_item(cls, prompt_item: "PromptItem") -> None:
        """
        PromptItemsテーブルのデータを更新する
        idに一致したデータを更新する
        一致したデータが存在しない場合はinsertする
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        item = cls.get_prompt_item_by_id(prompt_item.id)
        if item is None:
            # データが存在しない場合はinsertする
            cur.execute('''
                INSERT INTO PromptItems (id, name, description, prompt, prompt_template_type, extended_properties_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (prompt_item.id, prompt_item.name, prompt_item.description, prompt_item.prompt,
                  prompt_item.prompt_template_type, prompt_item.extended_properties_json))
        else:
            # データが存在する場合はupdateする
            cur.execute('''
                UPDATE PromptItems SET name=?, description=?, prompt=?, prompt_template_type=?, extended_properties_json=?
                WHERE id=?
            ''', (prompt_item.name, prompt_item.description, prompt_item.prompt,
                  prompt_item.prompt_template_type, prompt_item.extended_properties_json, prompt_item.id))
        conn.commit()
        conn.close()

    @classmethod
    def delete_prompt_item(cls, id: str) -> None:
        """
        PromptItemsテーブルから指定されたIDのデータを削除する
        """
        conn = sqlite3.connect(MainDB.get_main_db_path())
        cur = conn.cursor()
        cur.execute("DELETE FROM PromptItems WHERE id=?", (id,))
        conn.commit()
        conn.close()
