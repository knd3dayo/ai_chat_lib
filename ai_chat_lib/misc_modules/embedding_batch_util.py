import os
import argparse
from dotenv import load_dotenv  # type:ignore
import pandas as pd  # type:ignore
from tqdm.asyncio import tqdm  # type:ignore
from ai_chat_lib.misc_modules.langchain_util import LangChainOpenAIClient, LangChainVectorStore, EmbeddingData

import logging
logger = logging.getLogger(__name__)

class EmbeddingBatchClient:
    """
    Embeddingのバッチ処理クライアント

    misc_modules.langchain_utilのLangChainUtilを利用してEmbeddingを更新する。
    """
    @classmethod
    def get_vector_store_path(cls, app_data_path: str) -> str:
        """
        アプリケーションデータパスからベクトルストアのパスを取得する。

        Args:
            app_data_path (str): アプリケーションデータのパス

        Returns:
            str: ベクトルストアのパス
        """
        return os.path.join(app_data_path, "vector_store")
    
    @classmethod
    def get_folder_names_file_path(cls, app_data_path: str) -> str:
        """
        アプリケーションデータパスからフォルダ名のファイルパスを取得する。

        Args:
            app_data_path (str): アプリケーションデータのパス

        Returns:
            str: フォルダ名のファイルパス
        """
        return os.path.join(app_data_path, "folder_names.json")
    
    def __init__(self, app_data_path) -> None:
        self.app_data_path = app_data_path
        self.client = LangChainOpenAIClient.create_from_env()
        self.vector_store = LangChainVectorStore(
            vector_store_url=self.get_vector_store_path(app_data_path),
            embedding_client=self.client,
            folder_names_file_path=self.get_folder_names_file_path(app_data_path)
        )

    def update_embeddings_from_excel(self, excel_path: str) -> None:
        """
        Excelファイルの各行のデータからEmbeddingDataを生成し、Embeddingを更新する。

        Args:
            excel_path (str): Excelファイルのパス
        """

        df = pd.read_excel(excel_path)
        # 列のチェック
        required_columns = ["content"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Excelファイルに必要な列 '{col}' が見つかりません。")
        # オプションの列
        optional_columns = ["folder_path", "description", "source_path"]
        for col in optional_columns:
            if col  in df.columns:
                logger.info(f"オプションの列 '{col}' が見つかりました。")
        
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_noinv_fmt}]"
        progress = tqdm(total=len(df), desc="Updating Embeddings", bar_format=bar_format)

        for idx, row in df.iterrows():
            params = row.to_dict()

            embedding_data = EmbeddingData(
                **params,
            )

            self.vector_store.update_embeddings([embedding_data])
            progress.update(1)
        progress.close()

        print(f"{len(df)} 件のEmbeddingを更新しました。")


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Local Embedding Uploader Tool")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to the Excel file")
    parser.add_argument("-d", "--app_data_path", type=str, default=os.getenv("APP_DATA_PATH"), help="Path to the application data directory")
    args = parser.parse_args()

    excel_path = args.file
    app_data_path = args.app_data_path
    if not app_data_path:
        print("Error: APP_DATA_PATH is not set in the environment variables.")
        return

    if not os.path.exists(excel_path):
        print(f"Error: Excel file '{excel_path}' does not exist.")
        return
    

    client = EmbeddingBatchClient(app_data_path)
    client.update_embeddings_from_excel(excel_path)

if __name__ == "__main__":

    main()


