import aiosqlite
import json
from typing import List, Union, Optional, ClassVar
import uuid
from pydantic import BaseModel, field_validator
from typing import Optional, List, Union

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

from ai_chat_lib.db_modules.vector_db_item import MainDB


class ContentFolder(BaseModel):
    '''
    以下のテーブル定義のデータを格納するクラス
    CREATE TABLE "ContentFoldersCatalog" (
        "id" TEXT NOT NULL CONSTRAINT "PK_ContentFoldersCatalog" PRIMARY KEY,
        "folder_type_string" TEXT NOT NULL,
        "parent_id" TEXT NULL,
        "folder_name" TEXT NOT NULL,
        "description" TEXT NOT NULL,
        "extended_properties_json" TEXT NOT NULL,
        "is_root_folder" INTEGER NOT NULL
    )
    '''
    
    id: Optional[str] = None
    folder_type_string: Optional[str] = None
    parent_id: Optional[str] = None
    folder_name: Optional[str] = None
    description: Optional[str] = None
    extended_properties_json: Optional[str] = None
    folder_path: Optional[str] = None
    is_root_folder: bool = False

    get_content_folder_requests_name: ClassVar[str] = "content_folder_requests"

    @field_validator("is_root_folder", mode="before")
    @classmethod
    def parse_is_root_folder(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, int):
            return bool(v)
        if isinstance(v, str):
            return v.upper() == "TRUE"
        return False

    @classmethod
    async def create_table(cls):
        # ContentFoldersテーブルが存在しない場合は作成する
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.cursor() as cur:
                # テーブルが存在するかチェック
                rows = await cur.execute('''
                    SELECT name FROM sqlite_master WHERE type="table" AND name="ContentFoldersCatalog"
                ''')
                table = await rows.fetchone()
                if table is not None:
                    # テーブルが存在する場合は何もしない
                    logger.debug("ContentFoldersCatalog table already exists.")
                    return
                else:
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS ContentFoldersCatalog (
                            id TEXT NOT NULL PRIMARY KEY,
                            folder_type_string TEXT NOT NULL,
                            parent_id TEXT NULL,
                            folder_name TEXT NOT NULL,
                            description TEXT NOT NULL,
                            extended_properties_json TEXT NOT NULL,
                            is_root_folder INTEGER NOT NULL DEFAULT 0
                        )
                    ''')
                    await conn.commit()
                    # インデックスを作成する
                    await cls.update_default_data()

    @classmethod
    async def update_default_data(cls):
        # parent_idにインデックスを追加
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                await cur.execute('''
                    CREATE INDEX IF NOT EXISTS idx_parent_id ON ContentFoldersCatalog (parent_id)
                ''')
                # folder_nameにインデックスを追加
                await cur.execute('''
                    CREATE INDEX IF NOT EXISTS idx_folder_name ON ContentFoldersCatalog (folder_name)
                ''')
                await conn.commit()

    @classmethod
    def get_content_folder_request_objects(cls, request_dict: dict) -> List["ContentFolder"]:
        '''
        {"content_folder_requests": [] }の形式で渡される
        '''
        content_folders = request_dict.get(cls.get_content_folder_requests_name, None)
        if not content_folders:
            raise ValueError("content_folder is not set.")
        return [cls(**item) for item in content_folders]
    async def to_dict(self) -> dict:
        result = self.model_dump()
        # folder_pathがなければidから取得
        if not result.get("folder_path") and self.id:
            content_folder_path = await ContentFolder.get_content_folder_path_by_id(self.id)
            if content_folder_path:
                result["folder_path"] = content_folder_path
        return result

    # idを指定して、idとfolder_nameとparent_idを取得する.再帰的に親フォルダを辿り、folderのパスを生成する
    @classmethod
    async def get_content_folder_path_by_id(cls, folder_id: str) -> Union[str, None]:

        async def get_folder_name_recursively(folder_id: str, paths: list[str]) -> list[str]:
            # データベースへ接続
            async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.cursor() as cur:

                    await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE id=?", (folder_id,))
                    row = await cur.fetchone()

                    # データが存在しない場合はNoneを返す
                    if row is None:
                        logger.info(f"Folder with id {folder_id} not found.")
                        return paths
                    
                    logger.info(f"Folder with id {folder_id} found.")

                    folder_dict = dict(row)
                    folder_name = folder_dict.get("folder_name", "")
                    parent_id = folder_dict.get("parent_id", "")

                    logger.info(f"Folder name: {folder_name}, Parent id: {parent_id}")
                    paths.append(folder_name)

                    # 親フォルダが存在する場合は再帰的に取得する
                    if parent_id:
                        paths = await get_folder_name_recursively(parent_id, paths)

            return paths

        # フォルダのパスを取得する
        paths = await get_folder_name_recursively(folder_id, [])
        if len(paths) == 0:
            logger.info(f"Folder with id {folder_id} not found.")
            return None
        # フォルダのパスを生成する
        folder_path = "/".join(reversed(paths))
        logger.info(f"get_content_folder_path_by_id: Folder path: {folder_path}")
        return folder_path

    # pathを指定して、pathにマッチするエントリーを再帰的に辿り、folderを取得する
    @classmethod
    async def get_content_folder_by_path(cls, folder_path: str, create: bool = False) -> Union["ContentFolder", None]:
        # フォルダのパスを分割する
        folder_names = folder_path.split("/")
        # ルートフォルダから順次フォルダ名を取得する
        parent_folder: Union[ContentFolder, None] = None
        for folder_name in folder_names:
            # データベースへ接続
            async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.cursor() as cur:
                    # parent_folderがNoneの場合は、ルートフォルダ. parent_idがNoneで、folder_name = nameのデータを取得する
                    if parent_folder is None:
                        await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id IS NULL AND folder_name=?", (folder_name,))
                    else:
                        # parent_folderが存在する場合は、parent_folderのidをparent_idとして、folder_name = nameのデータを取得する
                        folder_id = parent_folder.id
                        await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id=? AND folder_name=?", (folder_id, folder_name))
                    row = await cur.fetchone()

                    # データが存在しない場合、createがTrueの場合は新規作成する
                    if row is None:
                        if create:
                            logger.info(f"Folder {folder_name} not found. Creating new folder.")
                            # folder_type_stringは親フォルダを引き継ぐ。親フォルダがない場合は"default"を設定する
                            if parent_folder:
                                folder_type_string = parent_folder.folder_type_string
                            else:
                                # ルートフォルダの場合は、デフォルトのフォルダタイプを設定する
                                folder_type_string = "default"
                            new_folder = ContentFolder(
                                id=str(uuid.uuid4()),
                                folder_type_string=folder_type_string,
                                parent_id=parent_folder.id if parent_folder else None,
                                folder_name=folder_name,
                                description="",
                                extended_properties_json=json.dumps({}),
                                is_root_folder=(parent_folder is None)
                            )
                            await cls.update_content_folder(new_folder)
                            return new_folder
                        else:
                            logger.info(f"Folder {folder_name} not found. Returning None.")
                            return None
                    # データが存在する場合は、ContentFoldersCatalogオブジェクトを生成する
                    folder_dict = dict(row)
                    folder = ContentFolder(**folder_dict)
                    logger.info(f"Folder {folder_name} found with id {folder.id}.")
                    # parent_folderを更新する
                    parent_folder = folder
        # 最後に取得したフォルダを返す
        if parent_folder is None:
            logger.info(f"Folder {folder_path} not found.")
            return None
        logger.info(f"Folder {folder_path} found with id {parent_folder.id}.")
        return parent_folder

    @classmethod
    async def get_root_content_folders(cls) -> list["ContentFolder"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id IS NULL")
                rows = await cur.fetchall()
                root_folders = [ContentFolder(**dict(row)) for row in rows]

        return root_folders
    
    @classmethod
    async def get_content_folders(cls, include_path: bool = False) -> List["ContentFolder"]:
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentFoldersCatalog")
                rows = await cur.fetchall()
                folders = [ContentFolder(**dict(row)) for row in rows]

        # include_pathがTrueの場合は、folder_pathを設定する
        if include_path:
            for folder in folders:
                if folder.id:
                    folder.folder_path = await cls.get_content_folder_path_by_id(folder.id)
        return folders

    @classmethod
    async def get_content_folder_by_id(cls, folder_id: Union[str, None]) -> Union["ContentFolder", None]:
        if folder_id is None:
            return None
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            conn.row_factory = aiosqlite.Row 
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE id=?", (folder_id,))
                row = await cur.fetchone()

                # データが存在しない場合はNoneを返す
                if row is None or len(row) == 0:
                    return None

                folder_dict = dict(row)

        return ContentFolder(**folder_dict)

    @classmethod
    async def update_content_folder(cls, folder: "ContentFolder"):
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                id = None
                if folder.id:
                    folder_id_folder = await cls.get_content_folder_by_id(folder.id)
                    if folder_id_folder:
                        id = folder_id_folder.id
                # folder_pathが指定されている場合は、folder_pathからFolderを取得する
                elif folder.folder_path:
                    folder_path_folder = await cls.get_content_folder_by_path(folder.folder_path)
                    if folder_path_folder:
                        id = folder_path_folder.id

                if id is None:
                    logger.info(f"ContentFolder {folder.folder_name} is not exists. Create new folder.")
                    if not folder.id:
                        folder.id = str(uuid.uuid4())
                    sql = f"INSERT INTO ContentFoldersCatalog (id, folder_type_string, parent_id, folder_name, description, extended_properties_json) VALUES (?, ?, ?, ?, ?, ?)"
                    logger.info(f"SQL: {sql}")
                    insert_params = (folder.id, folder.folder_type_string, folder.parent_id, folder.folder_name, folder.description, folder.extended_properties_json)
                    logger.info(f"Params: {insert_params}")
                    await cur.execute(sql , insert_params)
                else:
                    # idが存在する場合は、更新処理を行う
                    folder.id = id
                    update_params = await folder.to_dict()
                    # folder_pathは、ContentFoldersCatalogのテーブルには存在しないので、リセットする
                    update_params["folder_path"] = None

                    folder.folder_path = None
                    logger.info(f"ContentFolder {folder.folder_name} is exists. Update folder.")
                    sql = MainDB.create_update_sql("ContentFoldersCatalog", "id", update_params)
                    logger.info(f"SQL: {sql}")
                    await cur.execute(sql)

                await conn.commit()

    @classmethod
    async def update_content_folder_by_path(cls, folder: "ContentFolder"):        
        folder_path = folder.folder_path
        if not folder_path:
            raise ValueError("folder_path is not set.")
        # folder_pathを分割する
        folder_names = folder_path.split("/")

        if len(folder_names) <= 1:
            # 現在の実装上、folder_path = ルートフォルダの階層の場合は処理不可
            raise ValueError("folder_path is root folder. Please set folder_path to child folder.")

        # 対象フォルダの上位階層のfolder_idをチェック. folder_idが存在しない場合は処理不可
        parent: Union[ContentFolder, None] = None
        for folder_level in range(len(folder_names) - 1):
            if folder_level == 0:
                folder_name = folder_names[folder_level]
            else:
                # 0からfolder_levelまでのフォルダ名を取得する
                folder_name = "/".join(folder_names[:folder_level + 1])

            # folder_nameを取得する
            parent = await cls.get_content_folder_by_path(folder_name)
            if not parent:
                raise ValueError(f"folder {folder_name} is not exists.")

        # folderの更新処理。parent_idを更新する
        if not parent:
            raise ValueError(f"parent folder {folder.folder_path} is not exists.")
        
        folder.parent_id = parent.id
        
        # folder_type_stringが指定されていない場合は、parentのfolder_type_stringを引き継ぐ
        if not folder.folder_type_string:
            folder.folder_type_string = parent.folder_type_string

        # update_content_folderを呼び出す
        await cls.update_content_folder(folder)

    @classmethod
    async def delete_content_folder(cls, folder: "ContentFolder"):
        delete_ids = []
        # folder_pathが指定されている場合は、folder_pathからFolderを取得する
        if folder.folder_path:
            folder_path_folder = await cls.get_content_folder_by_path(folder.folder_path)
            if not folder_path_folder:
                raise ValueError(f"folder {folder.folder_path} is not exists.")
            folder = folder_path_folder
        
        if folder.id:
            # childrenのidを取得する
            children_ids = await cls.get_content_folder_child_ids(folder.id)
            delete_ids = [folder.id] + children_ids
        else:
            raise ValueError("folder_id is not set.")
        # データベースへ接続
        async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
            async with conn.cursor() as cur:
                # delete_idsを削除する
                for delete_id in delete_ids:
                    await cur.execute("DELETE FROM ContentFoldersCatalog WHERE id=?", (delete_id,))
            await conn.commit()

    # childrenのidを取得する
    @classmethod
    async def get_content_folder_child_ids(cls, folder_id: str) -> list[str]:
        async def get_children_recursively(folder_id: str) -> list[str]:
            # データベースへ接続
            async with aiosqlite.connect(MainDB.get_main_db_path()) as conn:
                conn.row_factory = aiosqlite.Row
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM ContentFoldersCatalog WHERE parent_id=?", (folder_id,))
                    rows = await cur.fetchall()
                    rows = list(rows)

                    # データが存在しない場合は空のリストを返す
                    if len(rows) == 0:
                        return []

                    children = []
                    for row in rows:
                        folder_dict = dict(row)
                        children.append(folder_dict["id"])
                        children.extend(await get_children_recursively(folder_dict["id"]))
            return children
        
        # フォルダの子供を取得する
        children = await get_children_recursively(folder_id)
        return children

    @classmethod
    async def get_content_folder_ids_by_path(cls, folder_path: str) -> list[str]:
        # フォルダのパスを分割する
        folder_names = folder_path.split("/")

        folder_ids = []
        # フォルダ階層毎のfolder_idを取得して、folder_idsに追加する
        # 例： aaa/bbb/ccc の場合、aaaのfolder_idを取得して、aaa/bbbbのfolder_idを取得して、aaa/bbb/cccのfolder_idを取得する
        for folder_level in range(len(folder_names)):
            if folder_level == 0:
                folder_name = folder_names[folder_level]
            else:
                # 0からfolder_levelまでのフォルダ名を取得する
                folder_name = "/".join(folder_names[:folder_level + 1])

            id = await cls.get_content_folder_by_path(folder_name)
            folder_ids.append(id)

        return folder_ids


    @classmethod
    async def get_root_content_folders_api(cls) -> dict:
        content_folders = await cls.get_root_content_folders()
        result = {}
        result["content_folders"] = [await item.to_dict() for item in content_folders]
        return result

    @classmethod
    async def get_content_folders_api(cls) -> dict:
        content_folders = await cls.get_content_folders()
        result = {}
        result["content_folders"] = [await item.to_dict() for item in content_folders]
        return result

    @classmethod
    async def get_content_folder_by_id_api(cls, request_json: str) -> dict:
        request_dict: dict = json.loads(request_json)
        content_folder_id = cls.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder = await cls.get_content_folder_by_id(content_folder_id)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] = await content_folder.to_dict()
        return result

    @classmethod
    async def update_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = cls.get_content_folder_request_objects(request_dict)
        for content_folder in content_folders:
            await cls.update_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    async def delete_content_folders_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folders = cls.get_content_folder_request_objects(request_dict)
        for content_folder in content_folders:
            await cls.delete_content_folder(content_folder)
        result: dict = {}
        return result

    @classmethod
    async def get_content_folder_by_path_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_path = request_dict.get("content_folder_path", None)
        if not content_folder_path:
            raise ValueError("content_folder_path is not set")
        content_folder = await cls.get_content_folder_by_path(content_folder_path)
        result: dict = {}
        if content_folder is not None:
            result["content_folder"] = await content_folder.to_dict()
        return result

    @classmethod
    async def get_content_folder_path_by_id_api(cls, request_json: str):
        request_dict: dict = json.loads(request_json)
        content_folder_id = cls.get_content_folder_request_objects(request_dict)[0].id
        if not content_folder_id:
            raise ValueError("content_folder_id is not set")
        content_folder_path = await cls.get_content_folder_path_by_id(content_folder_id)
        result: dict = {}
        if content_folder_path is not None:
            result["content_folder_path"] = content_folder_path
        return result

