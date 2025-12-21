from typing import Sequence
from fastapi import FastAPI
from ai_chat_explorer_lib.db.prompt_item import PromptItem

import ai_chat_explorer_lib.model as model_base

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()

@app.get('/get_prompt_items')
async def get_prompt_items() -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.get_prompt_items()
    return response

@app.get('/get_prompt_item_by_id')
async def get_prompt_item(item_id: str) -> model_base.PromptItemModel | None:
    response = await PromptItem.get_prompt_item_by_id(item_id)
    return response

@app.post('/update_prompt_items')
async def update_prompt_items(items: Sequence[model_base.PromptItemModel]) -> Sequence[model_base.PromptItemModel]:
    response = await PromptItem.update_prompt_items(items)
    return response

@app.delete('/delete_prompt_items')
async def delete_prompt_items(items: Sequence[model_base.PromptItemModel]) -> None:
    response = await PromptItem.delete_prompt_items(items)
    return response
