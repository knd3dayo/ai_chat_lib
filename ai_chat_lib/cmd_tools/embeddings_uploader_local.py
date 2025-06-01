import pandas as pd
from typing import List, Optional
import uuid
import asyncio

from ai_chat_lib.db_modules.content_folders_catalog import ContentFoldersCatalog
from ai_chat_lib.db_modules.embedding_data import EmbeddingData
from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
from ai_chat_lib.llm_modules.openai_util import OpenAIProps


import argparse
import os
import asyncio
from dotenv import load_dotenv

from ai_chat_lib.db_modules.content_folders_catalog import ContentFoldersCatalog
from ai_chat_lib.db_modules.embedding_data import EmbeddingData
from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
from ai_chat_lib.llm_modules.openai_util import OpenAIProps
import pandas as pd
from typing import Optional
import uuid


async def update_embeddings_from_excel(
    excel_path: str,
    name: str = "default",
    model: str = "text-embedding-3-large",
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

    openai_props = OpenAIProps.create_from_env()

    for idx, row in df.iterrows():
        content = row.get("content")
        if not content or not isinstance(content, str) or content.strip() == "":
            # contentが無いか空文字の場合はスキップ
            continue

        folder_path = row.get("folder_path")
        folder_id: Optional[str] = None
        if folder_path and isinstance(folder_path, str) and folder_path.strip() != "":
            folder = ContentFoldersCatalog.get_content_folder_by_path(folder_path.strip())
            if folder:
                folder_id = folder.id

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
            folder_id=folder_id or "",
            content=content.strip(),
            description=description or "",
            source_path=source_path or "",
        )

        await LangChainUtil.update_embeddings(openai_props, embedding_data)

    print(f"{len(df)} 件のEmbeddingを更新しました。")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Local Embedding Uploader Tool")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to the Excel file")
    parser.add_argument("-n", "--name", type=str, default="default", help="EmbeddingData name")
    parser.add_argument("-m", "--model", type=str, default="text-embedding-3-large", help="EmbeddingData model")
    args = parser.parse_args()

    excel_path = args.file
    name = args.name
    model = args.model

    if not os.path.exists(excel_path):
        print(f"Error: Excel file '{excel_path}' does not exist.")
        return

    asyncio.run(update_embeddings_from_excel(excel_path, name, model))


if __name__ == "__main__":
    main()
