import pandas as pd
from typing import List, Optional
import uuid
import os
import asyncio
import argparse
from dotenv import load_dotenv
import pandas as pd

from ai_chat_lib.db_modules.content_folder import ContentFolder
from ai_chat_lib.langchain_modules.embedding_data import EmbeddingData
from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
from ai_chat_lib.llm_modules.openai_util import OpenAIProps
from ai_chat_lib.cmd_tools.client_util import init_app

async def update_embeddings_from_excel(
    excel_path: str,
    name: str = "default",
    model: str = "text-embedding-3-small",
) -> None:
    """
    Excelファイルの各行のデータからEmbeddingDataを生成し、Embeddingを更新する。

    Args:
        excel_path (str): Excelファイルのパス
        name (str): EmbeddingDataのname
        model (str): EmbeddingDataのmodel

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

    openai_props = OpenAIProps.create_from_env()

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

        embedding_data = EmbeddingData(
            name=name,
            model=model,
            source_id=source_id,
            folder_path=folder_path or "",
            content=content.strip(),
            description=description or "",
            source_path=source_path or "",
        )

        await LangChainUtil.update_embeddings(openai_props, embedding_data)

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

    asyncio.run(update_embeddings_from_excel(excel_path, name, model))


if __name__ == "__main__":
    asyncio.run(main())
