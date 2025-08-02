from typing import Optional, Union, ClassVar
from pydantic import BaseModel, Field
import aiosqlite
import json
import uuid
from ai_chat_lib.resouces.resource_util import get_string_resources
from ai_chat_lib.db_modules.main_db import MainDB

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

"""
以下のフィールドを持つPydanticモデルを定義します。
description: str
content: str
tags: str
source_application_name: str
source_application_title: str
start_time_str: str
end_time_str: str
enable_start_time: bool
enable_end_time: bool
exclude_description: bool
exclude_content: bool
exclude_tags: bool
exclude_source_application_name: bool
exclude_source_application_title: bool
"""
class SearchCondition(BaseModel):
    description: str
    content: str
    tags: str
    source_application_name: str
    source_application_title: str
    start_time_str: str
    end_time_str: str
    enable_start_time: bool
    enable_end_time: bool
    exclude_description: bool
    exclude_content: bool
    exclude_tags: bool
    exclude_source_application_name: bool
    exclude_source_application_title: bool