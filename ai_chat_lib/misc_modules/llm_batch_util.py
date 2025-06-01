
import sys
from typing import Any, Callable, Union
import asyncio

import pandas as pd  # type:ignore
from tqdm.asyncio import tqdm  # type:ignore
from openai import AsyncAzureOpenAI, RateLimitError

class LLMBatchClient:
    """
    LLM Batch Client for processing data with Azure OpenAI.

    Attributes:
        client: The Azure OpenAI client instance.
        model: The model to be used for processing.
        json_mode: Flag to indicate if the response should be in JSON format.
        max_concurrent: Maximum number of concurrent requests.
        post_processing: Optional function for post-processing results.
        _input_df: Input DataFrame containing data to be processed.
        _total_rows: Total number of rows in the input DataFrame.
    """

    def __init__(self, api_key: str, endpoint: str, version: str, model: str):
        client_params: dict[str, Any] = {}
        client_params["azure_endpoint"] = endpoint
        client_params["api_version"] = version
        client_params["api_key"] = api_key
        self.client = AsyncAzureOpenAI(**client_params)

        self.model: str = model
        self.json_mode: int = False
        self.max_concurrent: int = 16
        self.post_processing: Union[Callable, None] = None

        self.__input_df: Union[pd.DataFrame, None] = None
        self.__total_rows: int = 0

    async def run_chat(self, prompt_template: str, content: str) -> str:
        """
        Run a chat completion with the given prompt template and content.

        Args:
            prompt_template (str): The template for the prompt.
            content (str): The content to be processed.

        Returns:
            str: The response content from the chat completion.
        """
        content = f"{prompt_template}\n----\n{content}"

        chat_params: dict[str, Any] = {}
        chat_params["model"] = self.model
        chat_params["messages"] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": content
                    }
                ]
            }
        ]

        if self.json_mode:
            chat_params["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**chat_params)
        result = response.choices[0].message.content

        return result

    async def _execute_process_row(self, prompt_text: str, index: int, row: pd.Series, input_column_name: str):
        """
        Execute the processing of a single row in the input DataFrame.

        Args:
            prompt_text (str): The prompt text to be used for processing.
            index (int): The index of the row being processed.
            row (pd.Series): The row data to be processed.
            input_column_name (str): The name of the input column.

        Returns:
            tuple: A tuple containing the index and the processed result.
        """
        content = row[input_column_name]
        result = await self.run_chat(prompt_text, content)
        if self.post_processing:
            result = self.post_processing(result)

        return index, result

    async def execute_batch(
        self, prompt_text: str, input_column_name: str, output_column_name: str
    ) -> pd.DataFrame:
        """
        Execute batch processing on the input DataFrame.

        Args:
            prompt_text (str): The prompt text to be used for processing.
            input_column_name (str): The name of the input column.
            output_column_name (str): The name of the output column.

        Returns:
            pd.DataFrame: The updated DataFrame with processed results.
        """
        if self.__input_df is None:
            raise ValueError("input data frame is None")

        progress = tqdm(total=self.__total_rows)
        progress.bar_format = "{l_bar}{bar}|{n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_noinv_fmt}]"

        # セマフォ
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def sem_task(prompt_text, index, row, input_column_name):
            async with semaphore:
                task_result = None
                retries = 0
                while retries < 10:
                    try:
                        task_result = await self._execute_process_row(prompt_text, index, row, input_column_name)
                        break
                    except RateLimitError:
                        wait_time = 2 ** retries
                        print(f"RateLimitError occurred. Waiting for {wait_time} seconds before retrying.", file=sys.stderr)
                        retries += 1
                        await asyncio.sleep(wait_time)
                    except Exception as e:
                        import traceback
                        print(f"An error occurred: {e}")
                        task_result = None
                        raise e

                if task_result is None:
                    raise ValueError(f"An error occurred while processing row {index}.")
                progress.update(1)
                return task_result

        # 非同期タスクを作成
        tasks = [
            sem_task(prompt_text, index, row, input_column_name) for index, row in self._input_df.iterrows()
        ]

        # タスクを並列実行
        results = await asyncio.gather(*tasks)

        progress.close()

        # 結果をデータフレームに追加
        for index, result_row in results:
            self.__input_df.at[index, output_column_name] = result_row

        return self.__input_df
    
    
    def load_df(self, input_df: pd.DataFrame):
        """
        Load the input DataFrame for processing.

        Args:
            input_df (pd.DataFrame): The DataFrame containing input data.
        """
        self._input_df = input_df
        self._total_rows = len(self._input_df)

    def execute_batch_with_excel(
        self, prompt: str, input_file_name: str,
        input_data_column: str, output_data_column: str,
        output_file_name: str
    ):
        """
        Execute batch processing using an Excel file as input and output.

        Args:
            prompt (str): The prompt to be used for processing.
            input_file_name (str): The name of the input Excel file.
            input_data_column (str): The name of the column containing input data.
            output_data_column (str): The name of the output column.
            output_file_name (str): The name of the output Excel file.
        """
        # Excelファイルを読み込み
        self.load_df(pd.read_excel(input_file_name))

        # AIによる処理
        output_data_frame = asyncio.run(
            self.execute_batch(prompt, input_data_column, output_data_column)
        )

        # 更新されたデータフレームを新しいExcelファイルに保存
        output_data_frame.to_excel(output_file_name, index=False, engine='xlsxwriter')
