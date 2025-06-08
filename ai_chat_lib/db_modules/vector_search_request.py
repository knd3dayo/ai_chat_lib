from typing import List, Union, Optional, ClassVar
from pydantic import BaseModel, Field
from typing import Optional, List
from typing import Optional
from typing import Optional, Union, List
from typing import Optional, List, Dict, Any, Union
from ai_chat_lib.db_modules.vector_db_item import VectorDBItem
from ai_chat_lib.db_modules.content_folders_catalog import ContentFoldersCatalog
import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class VectorSearchRequest(BaseModel):
    name: str = Field(
        default="default",
        description="Name of the vector search request. This is used to identify the request in the system."
    )
    query: str = Field(
        ...,
        description="The query string to search for in the vector database. This is the main input for the vector search."
    )
    model: str = Field(
        default="text-embedding-3-small",
        description="The model to use for vector embedding. Default is 'text-embedding-ada-002'."
    )
    search_kwargs: Dict[str, Any] = Field(default_factory=dict)
    vector_db_item: Optional["VectorDBItem"] = None

    vector_search_requests_name: ClassVar[str] = "vector_search_requests"

    @classmethod
    async def get_vector_search_requests_objects(cls, request_dict: dict) -> List["VectorSearchRequest"]:
        '''
        {"vector_search_requests": [{...}, ...]} の形式で渡される
        '''
        request: Union[List[dict], None] = request_dict.get(cls.vector_search_requests_name, None)
        if not request:
            logger.info("vector search request is not set. skipping.")
            return []
        vector_search_requests = []
        for item in request:
            vector_search_request = VectorSearchRequest(**item)
            # search_kwargsのアップデート
            vector_search_request.search_kwargs = await vector_search_request.__update_search_kwargs(vector_search_request.search_kwargs)
            vector_search_requests.append(vector_search_request)
        return vector_search_requests

    async def __update_search_kwargs(self, kwargs: dict) -> dict:
        filter = kwargs.get("filter", None)
        if not filter:
            logger.debug("__update_search_kwargs: filter is not set.")
            return kwargs
        folder_path = filter.get("folder_path", None)
        if folder_path:
            logger.info(f"__update_search_kwargs: folder_path: {folder_path}")
            temp_folder = await ContentFoldersCatalog.get_content_folder_by_path(folder_path)
            if temp_folder and temp_folder.id:
                kwargs["filter"]["folder_id"] = temp_folder.id
            kwargs["filter"].pop("folder_path", None)
        else:
            logger.info("__update_search_kwargs: folder_path is not set.")
        return kwargs

    async def get_vector_db_item(self) -> "VectorDBItem":
        if self.vector_db_item:
            return self.vector_db_item
        vector_db_item = await VectorDBItem.get_vector_db_by_name(self.name)
        if not vector_db_item:
            raise ValueError("VectorDBItem is not found.")
        return vector_db_item

    def to_dict(self) -> dict:
        return self.model_dump()
