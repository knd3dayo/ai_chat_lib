from typing import Sequence
from fastapi import FastAPI
from ai_chat_explorer_lib.db.search import SearchRule

import ai_chat_explorer_lib.model as model_base


import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()

########################
# SearchRule関連
########################
@app.get('/api/get_search_rules')
async def get_search_rules() -> Sequence[model_base.SearchRuleModel]:
    response = await SearchRule.get_search_rules()
    return response

@app.post('/api/update_search_rules')
async def update_search_rules(rules: Sequence[model_base.SearchRuleModel]) -> Sequence[model_base.SearchRuleModel]:
    response = await SearchRule.update_search_rules(rules)
    return response

@app.delete('/api/delete_search_rules')
async def delete_search_rules(rules: Sequence[model_base.SearchRuleModel]) -> None:
    response = await SearchRule.delete_search_rules(rules)
    return response
