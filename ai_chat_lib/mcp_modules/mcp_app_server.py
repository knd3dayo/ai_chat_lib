
import os, sys
from typing import Annotated
from fastmcp import FastMCP
from pydantic import Field
from ai_chat_lib.autogen_modules.default_tools import search_wikipedia_ja
mcp = FastMCP("Demo 🚀")

@mcp.tool()
def search_wikipedia_ja_mcp(
    query: Annotated[str, Field(description="String to search for")], 
    lang: Annotated[str, Field(description="Language of Wikipedia")], 
    num_results: Annotated[int, Field(description="Maximum number of results to display")]
    ) -> Annotated[list[str], Field(description="List of related articles from Wikipedia")]:
    """
    This function searches Wikipedia with the specified keywords and returns related articles.
    """
    return search_wikipedia_ja(query, lang, num_results)

if __name__ == "__main__":
    # 第１引数はAPP_DATA_PATH
    if len(sys.argv) > 1:
        os.environ["APP_DATA_PATH"] = sys.argv[1]

    # APP_DATA_PATHを取得
    app_data_path = os.getenv("APP_DATA_PATH", None)
    if not app_data_path:
        raise ValueError("APP_DATA_PATH is required")

    mcp.run(transport="sse", port=5001)