import pandas as pd
import uuid
import os
import asyncio
import argparse
from dotenv import load_dotenv
import pandas as pd

from vector_search_mcp.model.models import VectorDBItemBase
from vector_search_mcp.util.vector_db_client import VectorDBClient
from vector_search_mcp.langchain.langchain_client import LangChainOpenAIClient
from ai_chat_lib.cmd_tools.client_util import init_app
from api_modules.ai_app_data import AIApppEmbeddingData
async def update_embeddings_from_excel(
    excel_path: str,
    vector_db_name: str = "default",
) -> None:
    """
    Excelファイルの各行のデータからEmbeddingDataを生成し、Embeddingを更新する。

    Args:
        excel_path (str): Excelファイルのパス
        vector_db_name (str): EmbeddingDataのvector_db_name

    Excelファイルの必須列:
        - content: 埋め込み対象のテキスト

    任意列:
        - folder_path: フォルダパス（ContentFolderCatalogのfolder_id取得に使用）
        - description: 説明文
        - source_path: ソースパス
    """
    df = pd.read_excel(excel_path)
    # content列が存在するか確認
    if "content" not in df.columns:
        raise ValueError("Excel file must contain a 'content' column.")

    client = LangChainOpenAIClient()
    vector_db_item = VectorDBItemBase()

    vector_db_client = VectorDBClient(langchain_openai_client=client, vector_dbs=[vector_db_item])

    for idx, row in df.iterrows():
        content = row.get("content")
        if not content or not isinstance(content, str) or content.strip() == "":
            # contentが無いか空文字の場合はスキップ
            continue

        folder_path = row.get("folder_path")

        description = row.get("description")
        if description is not None and not isinstance(description, str):
            description = str(description)

        source_path = row.get("source_path")
        if source_path is not None and not isinstance(source_path, str):
            source_path = str(source_path)

        source_id = str(uuid.uuid4())
        metadata = {
            "folder_id": folder_path if folder_path else "",
            "source_type": 0,  # デフォルト値
            "description": description if description else "",
            "source_path": source_path if source_path else "",
            "image_url": "",
        }
        embedding_data = AIApppEmbeddingData(
            vector_db_name=vector_db_name,
            content=content.strip(),
            source_id=source_id,
            metadata=metadata,
        )
        await embedding_data.validate_metadata()

        await vector_db_client.update_embeddings(embedding_data)

    print(f"{len(df)} 件のEmbeddingを更新しました。")


async def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Local Embedding Uploader Tool")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to the Excel file")
    args = parser.parse_args()

    excel_path = args.file
    name = "default"
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    if not os.path.exists(excel_path):
        print(f"Error: Excel file '{excel_path}' does not exist.")
        return

    # アプリケーションの初期化
    await init_app()

    asyncio.run(update_embeddings_from_excel(excel_path, vector_db_name=name))


if __name__ == "__main__":
    asyncio.run(main())
