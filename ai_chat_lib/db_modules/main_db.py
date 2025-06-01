import sqlite3
import uuid
import os
from typing import Union

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

        
class MainDB:

    # main_dbへのパスを取得
    @classmethod
    def get_main_db_path(cls) -> str:
        app_data_path = os.getenv("APP_DATA_PATH", None)
        if not app_data_path:
            raise ValueError("APP_DATA_PATH is not set.")
        app_db_path = os.path.join(app_data_path, "server", "main_db", "server_main.db")

        return app_db_path

    @classmethod
    def __create_update_sql(cls, table_name: str, key: str, items: dict ) -> str:
        # itemsからkeyをpopする
        if key not in items:
            raise ValueError(f"{key} is not in items.")
        # itemsからkeyをpopする
        key_value = items.pop(key)
        key_str = ""
        if type(key_value) == str:
            key_str = f"{key} = '{key_value}'"
        else:
            key_str = f"{key} = {key_value}"

        # itemsの値を文字列に変換する
        items_str = ""
        for k, v in items.items():
            # Noneの場合はスキップ
            if v is None:
                continue
            if type(v) == str:
                items_str += f"{k} = '{v}', "
            else:
                items_str += f"{k} = {v}, "
        # itemsの最後のカンマを削除する
        items_str = items_str[:-2]
        # SQL文を生成する
        sql = f"UPDATE {table_name} SET {items_str} WHERE {key_str}"
        return sql
    
    @classmethod
    def __create_insert_sql(cls, table_name: str, items: dict) -> str:
        insert_str = ""
        for k, v in items.items():
            if type(v) == str:
                insert_str += f"{k} = '{v}', "
            else:
                insert_str += f"{k} = {v}, "
        # itemsの最後のカンマを削除する
        items_str = insert_str[:-2]
        # SQL文を生成する
        sql = f"INSERT INTO {table_name} SET {items_str}"
        return sql
    

    def __init__(self, db_path = ""):
        # db_pathが指定されている場合は、指定されたパスを使用する
        if db_path:
            self.db_path = db_path
        else:
            # db_pathが指定されていない場合は、環境変数から取得する
            self.db_path = MainDB.get_main_db_path()

    @classmethod
    def init_db_properties_table(cls):
        # DBPropertiesテーブルが存在しない場合は作成する
        conn = sqlite3.connect(cls.get_main_db_path())
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS DBProperties (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                value TEXT NOT NULL
            )
        ''')
        # version = 1を追加
        cur.execute('''
            INSERT OR IGNORE INTO DBProperties (id, name, value) VALUES (?, ?, ?)
        ''', (str(uuid.uuid4()), "version", "1"))

        conn.commit()
        conn.close()
    
    #########################################
    # DBProperties関連
    #########################################
    def get_db_properties(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM DBProperties")
        rows = cur.fetchall()
        db_properties = {row["name"]: row["value"] for row in rows}
        conn.close()

        return db_properties
    
    def get_db_property(self, name: str) -> Union[str, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()
        cur.execute("SELECT * FROM DBProperties WHERE name=?", (name,))
        row = cur.fetchone()

        # データが存在しない場合はNoneを返す
        if row is None or len(row) == 0:
            return None

        db_property_dict = dict(row)
        conn.close()

        return db_property_dict["value"]
    
    def update_db_property(self, name: str, value: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        if self.get_db_property(name) is None:
            cur.execute("INSERT INTO DBProperties (id, name, value) VALUES (?, ?, ?)", (str(uuid.uuid4()), name, value))
        else:
            cur.execute("UPDATE DBProperties SET value=? WHERE name=?", (value, name))
        conn.commit()
        conn.close()

    def delete_db_property(self, name: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM DBProperties WHERE name=?", (name,))
        conn.commit()
        conn.close()

