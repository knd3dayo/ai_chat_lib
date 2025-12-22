from fastapi import APIRouter, FastAPI

import ai_chat_explorer_lib.model as model_base


import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

router = APIRouter()

app = FastAPI()
app.include_router(router)

########################
# SearchRule関連
########################
@router.get('/get_search_rules')
async def get_search_rules() -> list[model_base.SearchRuleModel]:
    response = await model_base.SearchRuleModel.get_search_rules()
    return response

@router.post('/update_search_rules')
async def update_search_rules(rules: list[model_base.SearchRuleModel]):
    response = await model_base.SearchRuleModel.update_search_rules(rules)
    return response

@router.delete('/delete_search_rules')
async def delete_search_rules(name_list: list[str]) -> None:
    response = await model_base.SearchRuleModel.delete_search_rules(name_list)
    return response
