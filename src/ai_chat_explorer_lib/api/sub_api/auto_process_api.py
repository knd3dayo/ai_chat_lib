from typing import Sequence
from fastapi import APIRouter, FastAPI

from ai_chat_explorer_lib.db.auto_process import AutoProcessItem, AutoProcessRule
import ai_chat_explorer_lib.model as model_base

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

router = APIRouter()

app = FastAPI()
app.include_router(router)

@router.get('/get_auto_process_rules')
async def get_auto_process_rules() -> Sequence[model_base.AutoProcessRuleModel]:
    response = await AutoProcessRule.get_auto_process_rules()
    return response

@router.post('/update_auto_process_rules')
async def update_auto_process_rules(rules: Sequence[model_base.AutoProcessRuleModel]) -> Sequence[model_base.AutoProcessRuleModel]:
    response = await AutoProcessRule.update_auto_process_rules(rules)
    return response

@router.delete('/delete_auto_process_rules')
async def delete_auto_process_rules(rules: Sequence[model_base.AutoProcessRuleModel]) -> None:
    response = await AutoProcessRule.delete_auto_process_rules(rules)
    return response

@router.get('/get_auto_process_items')
async def get_auto_process_items() -> Sequence[model_base.AutoProcessItemModel]:
    response = await AutoProcessItem.get_auto_process_items()
    return response

@router.post('/update_auto_process_items')
async def update_auto_process_items(items: Sequence[model_base.AutoProcessItemModel]) -> Sequence[model_base.AutoProcessItemModel]:
    response = await AutoProcessItem.update_auto_process_items(items)
    return response

@router.delete('/delete_auto_process_items')
async def delete_auto_process_items(items: Sequence[model_base.AutoProcessItemModel]) -> None:
    response = await AutoProcessItem.delete_auto_process_items(items)
    return response
