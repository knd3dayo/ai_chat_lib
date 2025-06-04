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

def past_chat_history_vector_search(query: Annotated[str, "String to search for"]) -> list[str]:
    """
    過去のチャット履歴に関連するドキュメントを検索します。
    """
    global autogen_props
    from ai_chat_lib.db_modules import VectorDBItem
    from ai_chat_lib.langchain_modules.langchain_util import LangChainUtil
    from ai_chat_lib.autogen_modules import AutoGenProps
    from ai_chat_lib.llm_modules.openai_util import OpenAIProps

    props : AutoGenProps = autogen_props # type: ignore
    openai_props = OpenAIProps.create_from_env()

    if props.main_vector_db_id is None:
        raise ValueError("main_vector_db_id is not set.")
    main_vector_db_item = VectorDBItem.get_vector_db_by_id(props.main_vector_db_id)
    if main_vector_db_item is None:
        raise ValueError("main_vector_db_id is not set.")
    if props.chat_history_folder_id is None:
        raise ValueError("chat_history_folder_id is not set.")

    main_vector_db_item.folder_id = props.chat_history_folder_id

    vector_db_item_list = [] if main_vector_db_item is None else [main_vector_db_item]
    # vector_db_prop_listの各要素にinput_textを設定
    for request in props.vector_search_requests:
        request.query = query
    search_results = LangChainUtil.vector_search(openai_props, props.vector_search_requests)
    # Retrieve documents from result
    documents = search_results.get("documents", [])
    # Extract content of each document from documents
    result = [doc.get("content", "") for doc in documents]
    return result

