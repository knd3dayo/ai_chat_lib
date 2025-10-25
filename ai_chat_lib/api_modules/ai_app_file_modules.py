import json
import os
import base64
from extract_file_mcp.file_modules.file_util import FileUtil, ExcelUtil
from ai_chat_lib.api_modules.ai_app_data import AIAppData

class FileUtilAPI:

    @classmethod
    async def extract_text_from_file_async_api(cls, request_json: str) -> dict:
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # file_requestを取得
        file_request = AIAppData.get_file_request_objects(request_dict)
        # file_pathを取得
        filename = file_request.get("file_path", None)
        from typing import Optional
        text: Optional[str] = await FileUtil.extract_text_from_file_async(filename)
        return {"output": text}

    @classmethod
    async def extract_base64_to_text_async_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # file_requestを取得
        file_request = AIAppData.get_file_request_objects(request_dict)
        # extensionを取得
        extension = file_request.get("extension", None)
        # base64_dataを取得
        base64_data = file_request.get("base64_data", None)

        # サイズが0の場合は空文字を返す
        if not base64_data or len(base64_data) == 0:
            return ""

        # base64からバイナリデータに変換
        base64_data_bytes = base64.b64decode(base64_data)

        # 拡張子の指定。extensionがNoneまたは空の場合は設定しない.空でない場合は"."を先頭に付与
        suffix = ""
        if extension is not None and extension != "":
            suffix = "." + extension
        # base64データから一時ファイルを生成
        import aiofiles.tempfile
        async with aiofiles.tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=suffix) as temp:
            await temp.write(base64_data_bytes)
            await temp.close()
            # 一時ファイルからテキストを抽出
            temp_path = temp.name if isinstance(temp.name, str) else str(temp.name)
            text = await FileUtil.extract_text_from_file_async(temp_path)
            # 一時ファイルを削除
            os.remove(temp_path)
            return text

        return {"output": text}


    @classmethod
    def get_mime_type_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # file_requestを取得
        file_request = AIAppData.get_file_request_objects(request_dict)
        # file_pathを取得
        file_path = file_request.get("file_path", None)
        text = FileUtil.get_mime_type(file_path)
        return {"output": text}

class ExcelUtilAPI:

    @classmethod
    def get_sheet_names_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # excel_requestを取得
        file_path, _ = AIAppData.get_excel_request_objects(request_dict)
        text = ExcelUtil.get_sheet_names(file_path)
        return {"output": text}

    @classmethod
    def extract_excel_sheet_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # excel_requestを取得
        file_path, excel_request = AIAppData.get_excel_request_objects(request_dict)
        # excel_sheet_nameを取得
        sheet_name = excel_request.get("excel_sheet_name", "")

        text = ExcelUtil.extract_text_from_sheet(file_path, sheet_name)
        return {"output": text}

    @classmethod
    def export_to_excel_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        
        # file_pathとdata_jsonを取得
        file_path, dataJson = AIAppData.get_excel_request_objects(request_dict)
        ExcelUtil.export_to_excel(file_path, dataJson.get("rows",[]))
        # 結果用のdictを生成
        return {}

    @classmethod
    def import_from_excel_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # file_requestを取得
        file_path, _ = AIAppData.get_excel_request_objects(request_dict)
        # import_to_excelを実行
        data = ExcelUtil.import_from_excel(file_path)
        # 結果用のdictを生成
        result = {}
        result["rows"] = data
        return result

