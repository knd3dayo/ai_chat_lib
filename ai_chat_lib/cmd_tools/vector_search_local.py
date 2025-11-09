import argparse
import os
from dotenv import load_dotenv
from vector_search_mcp.util.vector_db_client import VectorDBClient
from vector_search_mcp.langchain.langchain_client import LangChainOpenAIClient
from vector_search_mcp.model.models import VectorDBItemBase
from api_modules.ai_app_data import AIAppVectorSearchRequest

def parse_args():
    parser = argparse.ArgumentParser(description="Local Vector Search Tool")
    parser.add_argument("-q", "--query", type=str, required=True, help="Search query string")
    parser.add_argument("-n", "--num_results", type=int, default=10, help="Number of search results to return")
    # APP_DATA_PATH
    parser.add_argument("-d", "--app_data_path", type=str, default=os.getenv("APP_DATA_PATH", ""), help="Path to the application data directory (default: APP_DATA_PATH environment variable)")
    parser.add_argument("-t", "--target_folder", type=str, default="", help="Target folder for vector search (optional)")
    return parser.parse_args()

async def main():
    # 環境変数を読み込む
    load_dotenv()
    args = parse_args()
    query = args.query
    num_results = args.num_results
    target_folder = args.target_folder

    if args.app_data_path:
        os.environ["APP_DATA_PATH"] = args.app_data_path

    # 環境変数APP_DATA_PATHが設定されているか確認
    app_data_path = os.getenv("APP_DATA_PATH")
    if not app_data_path:
        raise EnvironmentError("Environment variable APP_DATA_PATH is not set. Please set it before running this tool.")

    client = LangChainOpenAIClient()
    vector_db_item = VectorDBItemBase()
    vector_db_client = VectorDBClient(langchain_openai_client=client, vector_dbs=[vector_db_item])

    vector_search_request = AIAppVectorSearchRequest (
        vector_db_name="default",
        query=query,
        k=num_results,
        filter={},
    )
    if target_folder:
        vector_search_request.filter = {"folder_path": target_folder}

    await vector_search_request.validate_filter()

    # vector_searchを呼び出す
    results = await vector_db_client.vector_search(vector_search_request)

    # 結果を表示
    print(f"Search Query: {query}")
    print(f"Number of Results: {num_results}")
    print(f"Target Folder: {target_folder if target_folder else 'Not specified'}")
    print("Search Results:")
    print("--------------------------------------------------")
    for i, doc in enumerate(results, 1):
        print(f"Result {i}:")
        print(doc)
        print("--------------------------------------------------")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
