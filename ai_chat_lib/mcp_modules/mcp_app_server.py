
import os, sys
import asyncio
from typing import Annotated, Any
from dotenv import load_dotenv
import argparse
from fastmcp import FastMCP
from pydantic import Field
from ai_chat_lib.db_modules.main_db_util import MainDBUtil
from ai_chat_lib.db_modules.content_folder import ContentFolder

from web_search_mcp.web_modules.search_wikipedia_ja import search_wikipedia_ja
from extract_file_mcp.file_modules.file_util import FileUtil
from web_search_mcp.web_modules.web_util import WebUtil, WebSearchResult
from analyze_image_mcp.mcp_modules.mcp_app_server import analyze_image_mcp, analyze_two_images_mcp
from vector_search_mcp.langchain.langchain_util import LangChainUtil, LangChainOpenAIClient, VectorDBItemBase, VectorSearchRequest
from langchain_core.documents import Document

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
    ) -> Annotated[list[Document], Field(description="List of related documents from vector search")]:
    """
    This function performs a vector search on the specified text and returns the related documents.
    """
    client = LangChainOpenAIClient()
    vector_db_item = VectorDBItemBase()
    vector_search_request = VectorSearchRequest(
        query=query,
        search_kwargs={"k": num_results, "filter": {"folder_path": target_folder}} if target_folder else {"k": num_results},
        vector_db_item=vector_db_item
    )
    return await LangChainUtil.vector_search(client, vector_db_item, vector_search_request)

# フォルダ情報を取得するツールを登録
async def get_vector_folder_paths_mcp() -> Annotated[list[ContentFolder], Field(description="List of folders in the vector store")]:
    """
    This function retrieves the list of folder paths from the vector store.
    """
    return await ContentFolder.get_content_folders(include_path=True)

# duckduckgo_searchツールで検索した結果を返す
async def ddgs_search(
    query: Annotated[str, "The search query"],
    max_results: Annotated[int, "Maximum number of results to return"] = 10,
    site: Annotated[str, "Site to restrict the search to (optional)"] = "",
    detail: Annotated[bool, "If True, returns detailed results including the page content and a list of links from the result pages. Default is False"] = False
) -> Annotated[list[WebSearchResult], "List of search results from DuckDuckGo"]:
    return await WebUtil.ddgs_search(query, max_results, site, detail)
        
# 指定したURLのWebページからテキストとリンクを抽出するツールを登録
async def extract_webpage(
    url: Annotated[str, "URL of the web page to extract text and links from"]
) -> Annotated[dict[str, Any], "Dictionary containing 'output' (extracted text) and 'urls' (list of links with href and link text)"]:
    text, urls = await WebUtil.extract_webpage(url)
    result: dict[str, Any] = {}
    result["output"] = text
    result["urls"] = urls
    return result

# ファイルをダウンロードするツールを登録
def download_file_mcp(
    url: Annotated[str, "URL of the file to download"],
    save_path: Annotated[str, "Path to save the downloaded file"]
) -> Annotated[bool, "True if the file was downloaded successfully, False otherwise"]:
    return WebUtil.download_file(url, save_path)

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

    # MCP_TOOLSを取得
    mcp_tools_str = os.getenv("MCP_TOOLS", "")
    mcp_tools = [tool.strip() for tool in mcp_tools_str.split(",") if tool.strip()]
    print(f"MCP_TOOLS={mcp_tools}")
    #  MCP_TOOLSが指定されている場合は、ツールを登録
    if len(mcp_tools) > 0:
        for tool_name in mcp_tools:
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
        mcp.tool()(ddgs_search)
        mcp.tool()(extract_webpage)
        mcp.tool()(extract_text_from_file_mcp)
        mcp.tool()(download_file_mcp)
        mcp.tool()(analyze_image_mcp)
        mcp.tool()(analyze_two_images_mcp)

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
