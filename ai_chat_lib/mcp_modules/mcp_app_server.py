
import os, sys
import asyncio
from typing import Annotated, Any
from dotenv import load_dotenv
import argparse
from fastmcp import FastMCP
from pydantic import Field
from ai_chat_lib.web_modules.search_wikipedia_ja import search_wikipedia_ja
import ai_chat_lib.langchain_modules.vector_db_tools as vector_db_tools
from ai_chat_lib.db_modules.main_db_util import MainDBUtil
from ai_chat_lib.file_modules.file_util import FileUtil
from ai_chat_lib.db_modules.content_folder import ContentFolder
mcp = FastMCP("Demo 🚀") #type :ignore

async def extract_text_from_file_mcp(
    file_path: Annotated[str, Field(description="Path to the file to extract text from")]
    ) -> Annotated[str, Field(description="Extracted text from the file")]:
    """
    This function extracts text from a file at the specified path.
    """
    return await FileUtil.extract_text_from_file_async(file_path)

# toolは実行時にmcp.tool()で登録する。@mcp.toolは使用しない。
# Wikipedia検索ツールを登録
def search_wikipedia_ja_mcp(
    query: Annotated[str, Field(description="String to search for")], 
    lang: Annotated[str, Field(description="Language of Wikipedia")], 
    num_results: Annotated[int, Field(description="Maximum number of results to display")]
    ) -> Annotated[list[str], Field(description="List of related articles from Wikipedia")]:
    """
    This function searches Wikipedia with the specified keywords and returns related articles.
    """
    return search_wikipedia_ja(query, lang, num_results)

# ベクトル検索ツールを登録
async def vector_search_mcp(
    query: Annotated[str, Field(description="String to search for")], 
    num_results: Annotated[int, Field(description="Maximum number of results to display")],
    target_folder: Annotated[str, Field(description="Target folder for vector search (optional)")] = ""
    ) -> Annotated[list[dict[str, Any]], Field(description="List of related documents from vector search")]:
    """
    This function performs a vector search on the specified text and returns the related documents.
    """
    return await vector_db_tools.vector_search(query, num_results, target_folder)

# フォルダ情報を取得するツールを登録
async def get_vector_folder_paths_mcp() -> Annotated[list[ContentFolder], Field(description="List of folders in the vector store")]:
    """
    This function retrieves the list of folder paths from the vector store.
    """
    return await ContentFolder.get_content_folders(include_path=True)

# 引数解析用の関数
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MCP server with specified mode and APP_DATA_PATH.")
    # -m オプションを追加
    parser.add_argument("-m", "--mode", choices=["sse", "stdio"], default="stdio", help="Mode to run the server in: 'sse' for Server-Sent Events, 'stdio' for standard input/output.")
    # -d オプションを追加　APP_DATA_PATH を指定する
    parser.add_argument("-d", "--app_data_path", type=str, help="Path to the application data directory.")
    # 引数を解析して返す
    # -t tools オプションを追加 toolsはカンマ区切りの文字列. search_wikipedia_ja_mcp, vector_search, etc. 指定されていない場合は空文字を設定
    parser.add_argument("-t", "--tools", type=str, default="", help="Comma-separated list of tools to use, e.g., 'search_wikipedia_ja_mcp,vector_search_mcp'. If not specified, no tools are loaded.")
    # -p オプションを追加　ポート番号を指定する modeがsseの場合に使用.defaultは5001
    parser.add_argument("-p", "--port", type=int, default=5001, help="Port number to run the server on. Default is 5001.")
    # -v LOG_LEVEL オプションを追加 ログレベルを指定する. デフォルトは空白文字
    parser.add_argument("-v", "--log_level", type=str, default="", help="Log level to set for the server. Default is empty, which uses the default log level.")

    return parser.parse_args()

async def main():
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

    # ベクトルDBの初期化を行う
    await MainDBUtil.init(upgrade=True)

    # tools オプションが指定されている場合は、ツールを登録
    if args.tools:
        tools = [tool.strip() for tool in args.tools.split(",")]
        for tool_name in tools:
            # tool_nameという名前の関数が存在する場合は登録
            tool = globals().get(tool_name)
            if tool and callable(tool):
                mcp.tool()(tool)
            else:
                print(f"Warning: Tool '{tool_name}' not found or not callable. Skipping registration.")
    else:
        # デフォルトのツールを登録
        mcp.tool()(search_wikipedia_ja_mcp)
        mcp.tool()(vector_search_mcp)
        mcp.tool()(get_vector_folder_paths_mcp)

    if mode == "stdio":
        print(f"Running in stdio mode with APP_DATA_PATH: {app_data_path}")
        await mcp.run_async()
    elif mode == "sse":
        # port番号を取得
        port = args.port
        print(f"Running in SSE mode with APP_DATA_PATH: {app_data_path}")
        await mcp.run_async(transport="sse", port=port)


if __name__ == "__main__":
    asyncio.run(main())
