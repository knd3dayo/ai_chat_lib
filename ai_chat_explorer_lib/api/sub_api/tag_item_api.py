from fastapi import FastAPI

import ai_chat_explorer_lib.model as model_base


import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()
########################
# tag関連
########################
@app.get('/get_tag_items')
async def get_tag_items() -> list[model_base.TagItemModel]:
    response = await model_base.TagItemModel.get_tag_items()
    return response

@app.post('/update_tag_items')
async def update_tag_items(tag_items: list[model_base.TagItemModel]):
    response = await model_base.TagItemModel.update_tag_items(tag_items)
    return response

@app.delete('/delete_tag_items')
async def delete_tag_items(tag_names: list[str]) -> None:
    response = await model_base.TagItemModel.delete_tag_items(tag_names)
    return response
