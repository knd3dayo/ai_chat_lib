from typing import Callable, Annotated, Any, Union, List

def vector_search(
        query: Annotated[str, "String to search for"],
        num_results: Annotated[int, "Maximum number of results to display"],
        target_folder: Annotated[str, "Target folder for vector search (optional)"] = "",
        ) -> list[str]:
    """
    This function performs a vector search on the specified text and returns the related documents.
    """
    from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
    from ai_chat_lib.llm_modules.openai_util import OpenAIProps
    from ai_chat_lib.db_modules.vector_search_request import VectorSearchRequest
    from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
    
    # debug APP_DATA_PATHが設定されているか確認
    import os
    if "APP_DATA_PATH" not in os.environ:
        raise EnvironmentError("APP_DATA_PATH is not set in the environment variables.")
 
    openai_props = OpenAIProps.create_from_env()
    search_kwargs: dict[str, Any] = {
        "k": num_results,
    }
    if target_folder:
        # target_folderのパスからfolder_idを取得
        from ai_chat_lib.db_modules.content_folders_catalog import ContentFoldersCatalog
        folder = ContentFoldersCatalog.get_content_folder_by_path(target_folder)
        if folder:
            search_kwargs["filter"] = {"folder_id": folder.id}
        else:
            raise ValueError(f"Folder not found for path: {target_folder}")

    vector_search_request = VectorSearchRequest(
        name="default",
        query=query,
        model=openai_props.default_embedding_model,
        search_kwargs={
            "k": num_results,
            "filter": None,  # Optional filter can be added here
        },
    )
    search_results = LangChainUtil.vector_search(openai_props, [vector_search_request])
    # Retrieve documents from result
    documents = search_results.get("documents", [])
    # Extract content of each document from documents
    result = [doc.get("content", "") for doc in documents]
    return result

