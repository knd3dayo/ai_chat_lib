import os

from typing import Callable, Annotated, Any, Union, List
from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
from ai_chat_lib.llm_modules.openai_util import OpenAIProps
from ai_chat_lib.langchain_modules.vector_search_request import VectorSearchRequest
from ai_chat_lib.db_modules.content_folder import ContentFolder

async def vector_search(
        query: Annotated[str, "String to search for"],
        num_results: Annotated[int, "Maximum number of results to display"],
        target_folder: Annotated[str, "Target folder for vector search (optional)"] = "",
        ) -> list[dict[str, Any]]:
    """
    This function performs a vector search on the specified text and returns the related documents.
    """

    # debug APP_DATA_PATHが設定されているか確認
    if "APP_DATA_PATH" not in os.environ:
        raise ValueError("APP_DATA_PATH is not set in the environment variables.")
 
    openai_props = OpenAIProps.create_from_env()
    search_kwargs: dict[str, Any] = {
        "k": num_results,
    }


    if target_folder:
        # target_folderのパスからfolder_idを取得
        folder = await ContentFolder.get_content_folder_by_path(target_folder)
        if folder:
            search_kwargs["filter"] = {"folder_id": folder.id}
        else:
            raise ValueError(f"Folder not found for path: {target_folder}")


    vector_search_request = VectorSearchRequest(
        name="default",
        query=query,
        model=openai_props.default_embedding_model,
        search_kwargs=search_kwargs,
    )

    documents = await LangChainUtil.vector_search(openai_props, [vector_search_request])
    # Extract content of each document from documents

    result = [doc.model_dump() for doc in documents]
    return result

