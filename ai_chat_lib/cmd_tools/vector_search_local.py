import argparse
import os
from dotenv import load_dotenv
from ai_chat_lib.autogen_modules.vector_db_tools import vector_search

def parse_args():
    parser = argparse.ArgumentParser(description="Local Vector Search Tool")
    parser.add_argument("-q", "--query", type=str, required=True, help="Search query string")
    parser.add_argument("-n", "--num_results", type=int, default=10, help="Number of search results to return")
    # APP_DATA_PATH
    parser.add_argument("-d", "--app_data_path", type=str, default=os.getenv("APP_DATA_PATH", ""), help="Path to the application data directory (default: APP_DATA_PATH environment variable)")
    parser.add_argument("-t", "--target_folder", type=str, default="", help="Target folder for vector search (optional)")
    return parser.parse_args()

def main():
    # 環境変数を読み込む
    load_dotenv()
    args = parse_args()
    query = args.query
    num_results = args.num_results
    target_folder = args.target_folder

    # 環境変数APP_DATA_PATHが設定されているか確認
    app_data_path = os.getenv("APP_DATA_PATH")
    if not app_data_path:
        raise EnvironmentError("Environment variable APP_DATA_PATH is not set. Please set it before running this tool.")

    # vector_searchを呼び出す
    results = vector_search(query, num_results, target_folder)

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
    main()
