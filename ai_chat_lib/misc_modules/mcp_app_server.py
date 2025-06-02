
import os, sys
from typing import Annotated
from dotenv import load_dotenv
import argparse
from fastmcp import FastMCP
from pydantic import Field
from ai_chat_lib.misc_modules.langchain_util import LangChainOpenAIClient, LangChainVectorStore, EmbeddingData

mcp = FastMCP("Demo 🚀")

# ベクトル検索ツールを登録
@mcp.tool()
def vector_search_mcp(
    query: Annotated[str, Field(description="String to search for")], 
    num_results: Annotated[int, Field(description="Maximum number of results to display")],
    target_folder: Annotated[str, Field(description="Target folder for vector search (optional)")] = ""
    ) -> Annotated[list[EmbeddingData], Field(description="List of related documents from vector search")]:
    """
    This function performs a vector search on the specified text and returns the related documents.
    """
    client = LangChainOpenAIClient.create_from_env()
    vector_store = LangChainVectorStore(
        vector_store_url=LangChainVectorStore.get_vector_store_path(os.getenv("APP_DATA_PATH", "")),
        embedding_client=client,
        folder_names_file_path=LangChainVectorStore.get_folder_names_file_path(os.getenv("APP_DATA_PATH", ""))
    )
    params = {}
    params["query"] = query
    if num_results is None or num_results <= 0:
        num_results = 5
    params["num_results"] = num_results
    if target_folder:
        params["folder_path"] = target_folder
    
    return vector_store.vector_search(**params)

# 引数解析用の関数
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP server with specified mode and APP_DATA_PATH.")
    # -m オプションを追加
    parser.add_argument("-m", "--mode", choices=["sse", "stdio"], default="stdio", help="Mode to run the server in: 'sse' for Server-Sent Events, 'stdio' for standard input/output.")
    # -d オプションを追加　APP_DATA_PATH を指定する
    parser.add_argument("-d", "--app_data_path", type=str, help="Path to the application data directory.")
    # 引数を解析して返す
    # -p オプションを追加　ポート番号を指定する modeがsseの場合に使用.defaultは5001
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port number to run the server on. Default is 5001.")
    # -v LOG_LEVEL オプションを追加 ログレベルを指定する. デフォルトは空白文字
    parser.add_argument("-v", "--log_level", type=str, default="", help="Log level to set for the server. Default is empty, which uses the default log level.")

    return parser.parse_args()

if __name__ == "__main__":
    # load_dotenv() を使用して環境変数を読み込む
    load_dotenv()
    # 引数を解析
    args = parse_args()
    mode = args.mode
    app_data_path = args.app_data_path
    os.environ["APP_DATA_PATH"] = app_data_path if app_data_path else os.getenv("APP_DATA_PATH", "")

    # APP_DATA_PATHを取得
    app_data_path = os.getenv("APP_DATA_PATH", None)
    if not app_data_path:
        raise ValueError("APP_DATA_PATH is required")

    print(f"APP_DATA_PATH={app_data_path}")

    if mode == "stdio":
        print(f"Running in stdio mode with APP_DATA_PATH: {app_data_path}")
        mcp.run()
    elif mode == "sse":
        # port番号を取得
        port = args.port
        print(f"Running in SSE mode with APP_DATA_PATH: {app_data_path}")
        mcp.run(transport="sse", port=port)
