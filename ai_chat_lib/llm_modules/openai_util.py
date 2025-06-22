from dotenv import load_dotenv
import os, json
import base64
from mimetypes import guess_type
from typing import Any, Union, ClassVar
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any, Tuple, List

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class OpenAIProps(BaseModel):
    openai_key: str = Field(default="", alias="openai_key")
    azure_openai: bool = Field(default=False, alias="azure_openai")
    azure_openai_api_version: Optional[str] = Field(default=None, alias="azure_openai_api_version")
    azure_openai_endpoint: Optional[str] = Field(default=None, alias="azure_openai_endpoint")
    openai_base_url: Optional[str] = Field(default=None, alias="openai_base_url")

    default_completion_model: str = Field(default="gpt-4o", alias="default_completion_model")
    default_embedding_model: str = Field(default="text-embedding-3-small", alias="default_embedding_model")

    @model_validator(mode='before')
    def handle_azure_openai_bool_and_version(cls, values):
        azure_openai = values.get("azure_openai", False)
        if isinstance(azure_openai, str):
            values["azure_openai"] = azure_openai.upper() == "TRUE"
        if values.get("azure_openai_api_version") is None:
            values["azure_openai_api_version"] = "2024-02-01"
        return values


    def create_openai_dict(self) -> dict:
        completion_dict = {}
        completion_dict["api_key"] = self.openai_key
        if self.openai_base_url:
            completion_dict["base_url"] = self.openai_base_url
        return completion_dict

    def create_azure_openai_dict(self) -> dict:
        completion_dict = {}
        completion_dict["api_key"] = self.openai_key
        if self.openai_base_url:
            completion_dict["base_url"] = self.openai_base_url
        else:
            completion_dict["azure_endpoint"] = self.azure_openai_endpoint
            completion_dict["api_version"] = self.azure_openai_api_version
        return completion_dict

    @staticmethod
    def check_env_vars() -> bool:
        # OPENAI_API_KEYの存在を確認
        if "OPENAI_API_KEY" not in os.environ:
            logger.error("OPENAI_API_KEY is not set in the environment variables.")
            return False
        # AZURE_OPENAIの存在を確認
        if "AZURE_OPENAI" not in os.environ:
            logger.error("AZURE_OPENAI is not set in the environment variables.")
            return False
        if os.environ.get("AZURE_OPENAI", "false").lower() == "true":
            # AZURE_OPENAI_API_VERSIONの存在を確認
            if "AZURE_OPENAI_API_VERSION" not in os.environ:
                logger.error("AZURE_OPENAI_API_VERSION is not set in the environment variables.")
                return False
            # AZURE_OPENAI_ENDPOINTの存在を確認
            if "AZURE_OPENAI_ENDPOINT" not in os.environ:
                logger.error("AZURE_OPENAI_ENDPOINT is not set in the environment variables.")
                return False
        
        # DEFAULT_COMPLETION_MODELの存在を確認
        if "OPENAI_COMPLETION_MODEL" not in os.environ:
            logger.warning("OPENAI_COMPLETION_MODEL is not set in the environment variables. Defaulting to 'gpt-4o'.")
        # DEFAULT_EMBEDDING_MODELの存在を確認
        if "OPENAI_EMBEDDING_MODEL" not in os.environ:
            logger.warning("OPENAI_EMBEDDING_MODEL is not set in the environment variables. Defaulting to 'text-embedding-3-small'.")
        return True
    
    @staticmethod
    def create_from_env() -> 'OpenAIProps':
        load_dotenv()
        props: dict = {
            "openai_key": os.getenv("OPENAI_API_KEY"),
            "azure_openai": os.getenv("AZURE_OPENAI"),
            "azure_openai_api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
            "azure_openai_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "openai_base_url": os.getenv("OPENAI_BASE_URL"),
            "default_completion_model": os.getenv("OPENAI_COMPLETION_MODEL", "gpt-4o"),
            "default_embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        }
        openAIProps = OpenAIProps.model_validate(props)
        return openAIProps

    @staticmethod
    def local_image_to_data_url(image_path) -> str:
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{base64_encoded_data}"

    @staticmethod
    def create_openai_chat_parameter_dict(model: str, messages_json: str, temperature: float = 0.5, json_mode: bool = False) -> dict:
        params: dict[str, Any] = {}
        params["model"] = model
        params["messages"] = json.loads(messages_json)
        if temperature:
            params["temperature"] = str(temperature)
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        return params

    @staticmethod
    def create_openai_chat_parameter_dict_simple(model: str, prompt: str, temperature: Union[float, None] = 0.5, json_mode: bool = False) -> dict:
        messages = [{"role": "user", "content": prompt}]
        params: dict[str, Any] = {}
        params["messages"] = messages
        params["model"] = model
        if temperature:
            params["temperature"] = temperature
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        return params

    @staticmethod
    def create_openai_chat_with_vision_parameter_dict(
        model: str,
        prompt: str,
        image_file_name_list: List[str],
        temperature: float = 0.5,
        json_mode: bool = False,
        max_tokens=None
    ) -> dict:
        content: List[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image_file_name in image_file_name_list:
            image_data_url = OpenAIProps.local_image_to_data_url(image_file_name)
            content.append({"type": "image_url", "image_url": {"url": image_data_url}})
        messages = [{"role": "user", "content": content}]
        params: dict[str, Any] = {}
        params["messages"] = messages
        params["model"] = model
        if temperature:
            params["temperature"] = temperature
        if json_mode:
            params["response_format"] = {"type": "json_object"}
        if max_tokens:
            params["max_tokens"] = max_tokens
        return params

import json
from openai import AsyncOpenAI, AsyncAzureOpenAI
from pydantic import BaseModel, Field
from typing import Optional, Any, Tuple, List

class OpenAIClient:
    def __init__(self, props: OpenAIProps):
        
        self.props = props

    def get_completion_client(self) -> Union[AsyncOpenAI, AsyncAzureOpenAI]:
        
        if (self.props.azure_openai):
            params = self.props.create_azure_openai_dict()
            return AsyncAzureOpenAI(
                **params
            )

        else:
            params =self.props.create_openai_dict()
            return AsyncOpenAI(
                **params
            )

    def get_embedding_client(self) -> Union[AsyncOpenAI, AsyncAzureOpenAI]:
        if (self.props.azure_openai):
            params = self.props.create_azure_openai_dict()
            return AsyncAzureOpenAI(
                **params
            )
        else:
            params =self.props.create_openai_dict()
            return AsyncOpenAI(
                **params
            )

    async def list_openai_models_async(self) -> list[str]:
        
        client = self.get_completion_client()

        response = await client.models.list()

        # モデルのリストを取得する
        model_id_list = [ model.id for model in response.data]
        return model_id_list
