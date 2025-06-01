from typing import Optional, ClassVar
from pydantic import BaseModel
from typing import Optional

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class EmbeddingData(BaseModel):
    name: str
    model: str
    source_id: str
    folder_id: str 
    description: str = ""
    content: str
    source_path: str = ""
    git_repository_url: str = ""
    git_relative_path: str = ""
    image_url: str = ""

    embedding_request_name: ClassVar[str] = "embedding_request"

    @classmethod
    def get_embedding_request_objects(cls, request_dict: dict) -> "EmbeddingData":
        '''
        {"embedding_request": {}}の形式で渡される
        '''
        request: Optional[dict] = request_dict.get(cls.embedding_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return EmbeddingData(**request)

    def to_dict(self) -> dict:
        return self.model_dump()
