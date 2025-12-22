from typing import Sequence
from fastapi import APIRouter, FastAPI

import ai_chat_explorer_lib.model as model_base

# vector search util
import vector_search_util.api.api_server as vector_db_api
import vector_search_util.model as vector_model

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

router = APIRouter()

app = FastAPI()
app.include_router(router)

@router.get('/get_content_items')
async def get_content_items() -> Sequence[model_base.ContentItemModel]:
    return await model_base.ContentItemModel.get_items()

@router.get('/get_content_items_by_category_id')
async def get_content_items_by_category_id(category_id: str) -> Sequence[model_base.ContentItemModel]:
    return await model_base.ContentItemModel.get_items_by_category_id(category_id)

@router.get('/get_content_item_by_id')
async def get_content_item_by_id(item_id: str) -> model_base.ContentItemModel | None:
    return await model_base.ContentItemModel.get_item_by_id(item_id)

@router.post('/update_content_items')
async def update_content_items(content_items: Sequence[model_base.ContentItemModel]):
    await model_base.ContentItemModel.update_content_items(list(content_items))

@router.delete('/delete_content_items')
async def delete_content_items(items: Sequence[model_base.ContentItemModel]) -> None:
    await model_base.ContentItemModel.delete_content_items(list(items))

@router.get('/get_root_content_folders')
async def get_root_content_folders() -> Sequence[model_base.ContentFolderModel]:
    response = await model_base.ContentFolderModel.get_root_folders()
    return response

@router.get('/get_content_folders')
async def get_content_folders() -> Sequence[model_base.ContentFolderModel]:
    categories = await vector_db_api.get_categories()
    folders = [model_base.ContentFolderModel.from_category_data(cat) for cat in categories]
    return folders
    
@router.get('/get_content_folder_by_id')
async def get_content_folder_by_id(folder_id: str) -> model_base.ContentFolderModel | None:
    content_folder = await model_base.ContentFolderModel.get_folder_by_id(folder_id)
    return content_folder

@router.get('/get_content_folder_by_path')
async def get_content_folder_by_path(folder_path: str) -> model_base.ContentFolderModel | None:
    content_folder = await model_base.ContentFolderModel.get_folder_by_path(folder_path)
    return content_folder

@router.get('/get_content_folder_path_by_id')
async def get_content_folder_path_by_id(folder_id: str) -> str | None:
    content_folder_path = await model_base.ContentFolderModel.get_folder_path_by_id(folder_id)
    return content_folder_path

@router.get('/get_parent_content_folder_by_id')
async def get_parent_content_folder_by_id(folder_id: str) -> model_base.ContentFolderModel | None:
    parent_content_folder = await model_base.ContentFolderModel.get_parent_folder_by_id(folder_id)
    return parent_content_folder

@router.get('/get_child_content_folders_by_id')
async def get_child_content_folders_by_id(folder_id: str) -> Sequence[model_base.ContentFolderModel]:
    child_content_folders = await model_base.ContentFolderModel.get_child_folders_by_id(folder_id)
    return child_content_folders

@router.post('/update_content_folders')
async def update_content_folders(folders: list[model_base.ContentFolderModel]):
    await model_base.ContentFolderModel.update_folders(folders)

@router.delete('/delete_content_folders')
async def delete_content_folders(folders: list[model_base.ContentFolderModel]):
    await model_base.ContentFolderModel.delete_folders(folders)