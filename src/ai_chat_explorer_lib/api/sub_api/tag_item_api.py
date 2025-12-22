from fastapi import APIRouter, FastAPI

import ai_chat_explorer_lib.model as model_base


import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

router = APIRouter()

app = FastAPI()
app.include_router(router)
########################
# tag関連
########################
@router.get('/get_tag_items')
async def get_tag_items() -> list[model_base.TagItemModel]:
    response = await model_base.TagItemModel.get_tag_items()
    return response

@router.post('/update_tag_items')
async def update_tag_items(tag_items: list[model_base.TagItemModel]):
    response = await model_base.TagItemModel.update_tag_items(tag_items)
    return response

@router.delete('/delete_tag_items')
async def delete_tag_items(tag_names: list[str]) -> None:
    response = await model_base.TagItemModel.delete_tag_items(tag_names)
    return response
