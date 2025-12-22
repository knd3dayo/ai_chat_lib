from typing import Sequence
from fastapi import APIRouter, FastAPI
from ai_chat_explorer_lib.db.prompt_item import PromptItem

import ai_chat_explorer_lib.model as model_base

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

router = APIRouter()

app = FastAPI()
app.include_router(router)

@router.get('/get_prompt_items')
async def get_prompt_items() -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.get_prompt_items()
    return response

@router.get('/get_prompt_item_by_id')
async def get_prompt_item(item_id: str) -> model_base.PromptItemModel | None:
    response = await PromptItem.get_prompt_item_by_id(item_id)
    return response

@router.post('/update_prompt_items')
async def update_prompt_items(items: Sequence[model_base.PromptItemModel]) -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.update_prompt_items(items)
    return response

@router.delete('/delete_prompt_items')
async def delete_prompt_items(items: Sequence[model_base.PromptItemModel]) -> None:
    response = await PromptItem.delete_prompt_items(items)
    return response
