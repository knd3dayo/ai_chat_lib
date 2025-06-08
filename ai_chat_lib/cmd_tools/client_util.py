from typing import Optional, Union, Any
import json
import re
import os
import sys
import httpx  # type: ignore

from dotenv import load_dotenv
import pandas as pd  # type: ignore

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

async def init_app() -> None:
    """
    アプリケーション初期化時に呼び出される関数
    :return: None
    """
    # MainDBの初期化
    from ai_chat_lib.db_modules import MainDBUtil
    await MainDBUtil.init()
    print("MainDB initialized.")
    # 環境変数APP_DATA_PATHの確認
    __check_app_data_path()
    # LLMの環境変数の確認
    __check_llm_envvars()


def jsonc_load(file_path: str):
    """
    Load a JSON file with comments.
    :param file_path: Path to the JSON file.
    :return: Parsed JSON data.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        # Remove comments
        # remove single line comment
        content = re.sub(r'//.*?\n', '', content)
        # remove comment block
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return json.loads(content)

def jsonc_loads(json_str: str):
    """
    Load a JSON string with comments.
    :param json_str: JSON string.
    :return: Parsed JSON data.
    """
    # Remove comments
    # remove single line comment
    json_str = re.sub(r'//.*?\n', '', json_str)
    # remove comment block
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    return json.loads(json_str)

def load_default_json_template() -> dict:
    """
    Load the default JSON template from a file.
    :return: Parsed JSON data.
    """
    # templateファイル[request_template.jsonc]を読み込む。ファイルはこのスクリプトと同じディレクトリにあるものとする。
    json_template = jsonc_load(os.path.join(os.path.dirname(__file__), "request_template.jsonc"))
    return json_template

def __check_app_data_path():
    """
    環境変数APP_DATA_PATHが設定されているか確認する関数
    :return: APP_DATA_PATHの値
    """
    if not os.environ.get("APP_DATA_PATH", None):
        # 環境変数APP_DATA_PATHが指定されていない場合はエラー. APP_DATA_PATHの説明を出力するとともに終了する
        logger.error("APP_DATA_PATH is not set.")
        logger.error("APP_DATA_PATH is the path to the root directory where the application data is stored.")
        raise ValueError("APP_DATA_PATH is not set.")


def __check_llm_envvars():
    """
    環境変数が設定されているか確認する関数
    """
    AZURE_OPENAI=os.environ.get("AZURE_OPENAI", "False").upper() == "TRUE"
    OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", None) 
    OPENAI_COMPLETION_MODEL=os.environ.get("OPENAI_COMPLETION_MODEL", None)
    AZURE_OPENAI_ENDPOINT=os.environ.get("AZURE_OPENAI_ENDPOINT", None)
    AZURE_OPENAI_API_VERSION=os.environ.get("AZURE_OPENAI_API_VERSION", None)

    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is not set.")
    if OPENAI_COMPLETION_MODEL is None:
        raise ValueError("OPENAI_COMPLETION_MODEL is not set.")
    if AZURE_OPENAI and (AZURE_OPENAI_ENDPOINT is None or AZURE_OPENAI_API_VERSION is None):
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_VERSION must be set when AZURE_OPENAI is True.")
    
def __update_openai_props_by_envvars(json_template):
    load_dotenv()
    AZURE_OPENAI=os.environ.get("AZURE_OPENAI", "False").upper() == "TRUE"
    OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY", None) 
    OPENAI_COMPLETION_MODEL=os.environ.get("OPENAI_COMPLETION_MODEL", None)
    AZURE_OPENAI_ENDPOINT=os.environ.get("AZURE_OPENAI_ENDPOINT", None)
    AZURE_OPENAI_API_VERSION=os.environ.get("AZURE_OPENAI_API_VERSION", None)
    OPENAI_BASE_URL=os.environ.get("OPENAI_BASE_URL", None)

    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is not set.")
    if OPENAI_COMPLETION_MODEL is None:
        raise ValueError("OPENAI_COMPLETION_MODEL is not set.")

    # 環境変数から情報を取得する
    # openai_propsの設定
    json_template["openai_props"]["AzureOpenAI"] = AZURE_OPENAI
    json_template["openai_props"]["OpenAIKey"] = OPENAI_API_KEY
    json_template["openai_props"]["AzureOpenAIAPIVersion"] = AZURE_OPENAI_API_VERSION
    json_template["openai_props"]["AzureOpenAIEndpoint"] = AZURE_OPENAI_ENDPOINT
    json_template["openai_props"]["OpenAIBaseURL"] = OPENAI_BASE_URL

def create_vector_search_request_from_envvars() -> dict:
    json_template = load_default_json_template()
    # 環境変数から情報を取得する
    # openai_propsの設定
    __update_openai_props_by_envvars(json_template)

    load_dotenv()
    VECTOR_DB_NAME=os.environ.get("VECTOR_DB_NAME", "default") 
    OPENAI_EMBEDDING_MODEL=os.environ.get("OPENAI_EMBEDDING_MODEL", None)
    if OPENAI_EMBEDDING_MODEL is None:
        raise ValueError("OPENAI_EMBEDDING_MODEL is not set.")

    # 環境変数から情報を取得する
    # vector_search_requestsの設定
    json_template["vector_search_requests"] = []
    request: dict[str, Any]= {}
    request["name"] = VECTOR_DB_NAME
    request["model"] = OPENAI_EMBEDDING_MODEL
    request["search_kwargs"] = {}
    json_template["vector_search_requests"].append(request)

    return json_template

def prepare_vector_search_request(request_json_file: Union[str, None], query: Union[str, None], search_result_count: int, score_threshold: float, vector_db_folder: str) -> dict:
    """
    ベクトル検索リクエストを準備する関数
    :param request_json_file: JSONファイルのパス
    :param query: 検索文字列
    :param search_result_count: 検索結果の数
    :param score_threshold: スコアの閾値
    :param vector_db_folder: ベクトルDBの検索対象フォルダ
    :return: リクエスト辞書
    """
    
    if request_json_file:
        # JSONファイルからリクエストを作成する
        request_dict = create_base_request_from_json_file(request_json_file)
    else:
        # 環境変数からリクエストを作成する
        request_dict = create_vector_search_request_from_envvars()
    # queryを設定する
    if query:
        # queryを設定する
        for i in range(len(request_dict["vector_search_requests"])):
            request_dict["vector_search_requests"][i]["query"] = query

    if search_result_count:
        # search_result_countを設定する
        for i in range(len(request_dict["vector_search_requests"])):
            request_dict["vector_search_requests"][i]["search_kwargs"]["k"] = search_result_count

    if score_threshold:
        # score_thresholdを設定する
        for i in range(len(request_dict["vector_search_requests"])):
            request_dict["vector_search_requests"][i]["search_kwargs"]["score_threshold"] = score_threshold

    if vector_db_folder:
        # vector_db_folderを設定する
        for i in range(len(request_dict["vector_search_requests"])):
            request_dict["vector_search_requests"][i]["search_kwargs"]["filter"] = {"folder_path": vector_db_folder}


    return request_dict


def add_normal_chat_message(role: str, message: str, json_template: dict):
    """
    Add a message to the chat request in the JSON template.
    :param role: Role of the message (user, assistant, system).
    :param message: Content of the message.
    :param json_template: JSON template to update.
    """
    # メッセージを追加する
    content = [ {"type": "text", "text": message} ]
    json_template["chat_request"]["messages"].append({"role": role, "content": content})

def clear_normal_chat_messages(json_template: dict):
    """
    Clear the chat messages in the JSON template.
    :param json_template: JSON template to update.
    """
    # メッセージをクリアする
    json_template["chat_request"]["messages"] = []

def create_base_request_from_json_file(request_json_file: str) -> dict:
    """
    JSONファイルからリクエストを作成する関数
    :param request_json_file: JSONファイルのパス
    :return: リクエスト辞書
    """
    with open(request_json_file, "r", encoding="utf-8") as f:
        request_json = f.read()
        request_dict = json.loads(request_json)
    return request_dict

def create_normal_chat_request_from_envvars() -> dict:
    json_template = load_default_json_template()
    # 環境変数から情報を取得する
    # openai_propsの設定
    __update_openai_props_by_envvars(json_template)

    # chat_requestの設定
    load_dotenv()
    OPENAI_COMPLETION_MODEL=os.environ.get("OPENAI_COMPLETION_MODEL", None)
    json_template["chat_request"]["model"] = OPENAI_COMPLETION_MODEL
    json_template["chat_request"]["messages"] = []

    # vector_search_requestsの解除
    json_template["vector_search_requests"] = None

    return json_template

def prepare_normal_chat_request(request_json_file: Union[str, None], interactive_mode: bool, message: Union[str, None]) -> dict:
    """
    リクエストを準備する関数
    :param request_json_file: JSONファイルのパス
    :param interactive_mode: インタラクティブモードかどうか
    :param message: メッセージ
    :return: リクエスト辞書
    """
    
    if request_json_file:
        # JSONファイルからリクエストを作成する
        request_dict = create_base_request_from_json_file(request_json_file)
    else:
        # 環境変数からリクエストを作成する
        request_dict = create_normal_chat_request_from_envvars()

    if interactive_mode and message:
        # インタラクティブモードの場合はメッセージをクリアする
        clear_normal_chat_messages(request_dict)
        # メッセージを設定する
        add_normal_chat_message("user", message, request_dict)

    return request_dict

async def send_request(request_dict: dict, api_endpoint: str) -> dict:
    """
    リクエストを送信する関数
    :param request_dict: リクエスト辞書
    :param api_base: APIのURL
    :return: レスポンス辞書
    """

    # APIリクエスト 現時点では認証はなし
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    # APIリクエスト 現時点では認証はなし
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # APIリクエスト送信
    async with httpx.AsyncClient() as client:
        logger.debug(f"Request data: {request_dict}")
        response = await client.post(api_endpoint, headers=headers, json=request_dict, timeout=180)
        logger.debug(f"Response data: {response.text}")

    # レスポンスの取得
    if response.status_code != 200:
        raise ValueError(f"API request failed with status code {response.status_code}")
    
    # レスポンスのJSONをdictionaryに変換
    response_dict = response.json()  # response.json() は非同期ではない

    return response_dict

def print_response(response_dict: dict, output_file: Optional[str] = None) -> None:
    """
    レスポンスを表示する関数
    output_typeが指定されている場合、その形式で出力する
    対応する形式は以下の通り
    - tsv: テキスト形式で出力
    - csv: CSV形式で出力
    - xlsx: Excel形式で出力
    - その他: JSON形式で出力
    :param response_dict: レスポンス辞書
    :param output_file: 出力ファイル名
    :return: なし

    """
    if not output_file:
        print(json.dumps(response_dict, ensure_ascii=False, indent=4))
        return
    if output_file.endswith(".xlsx"):
        # Excel形式で出力
        df = pd.DataFrame(response_dict).replace('\x0d', '', regex=True)
        df.to_excel(output_file, index=False, engine='openpyxl')
    elif output_file.endswith(".tsv"):
        # テキスト形式で出力
        df = pd.DataFrame(response_dict)
        df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")
    elif output_file.endswith(".csv"):
        # CSV形式で出力
        df = pd.DataFrame(response_dict)
        df.to_csv(output_file, index=False, encoding="utf-8")
    else:
        with open(output_file, "w", encoding="utf-8", newline="") as output_stream:
            # デフォルトはJSON形式で出力
            json.dump(response_dict, output_stream, ensure_ascii=False, indent=4)

from typing import Sequence, Hashable

def prepare_folders_request(file_path: str) -> dict[str, Any]:
    """
    コンテンツフォルダのリクエストを準備する関数
    file_pathが指定されている場合はそのファイルを読み込み、リクエストを作成する。
    file_pathはjson、xlsxのいずれかの形式である必要がある。
    :param file_path: JSONまたはExcelファイルのパス
    :return: リクエスト辞書
    """
    records_dict: list[dict[Hashable, Any]] = []
    if not file_path:
        return {}

    if file_path.endswith(".json"):
        # JSONファイルからリクエストを作成する
        with open(file_path, "r", encoding="utf-8") as f:
            records_dict = json.load(f)
    elif file_path.endswith(".xlsx"):
        # Excelファイルからリクエストを作成する
        df = pd.read_excel(file_path)
        records_dict = df.to_dict(orient="records")
    else:
        raise ValueError("file_path must be a JSON or Excel file.")
    request_dict = {
        "content_folder_requests": records_dict
    }
    return request_dict
