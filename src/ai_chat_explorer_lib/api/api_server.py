import os
import signal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
import uvicorn

from ai_chat_explorer_lib.db.main_db_util import MainDBUtil

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()

########################
# OpenAI Chat関連
########################
from ai_chat_util.api.api_server import router as ai_chat_router
app.include_router(ai_chat_router, prefix="/ai_chat", tags=["ai_chat"])

########################
# AutoProcess関連
########################
from ai_chat_explorer_lib.api.sub_api.auto_process_api import router as auto_process_router
app.include_router(auto_process_router, prefix="/auto_process", tags=["auto_process"])

########################
# PromptItem関連
########################
from ai_chat_explorer_lib.api.sub_api.prompt_item_api import router as prompt_item_router
app.include_router(prompt_item_router, prefix="/prompt_item", tags=["prompt_item"])


########################
# ContentItem関連
########################
from ai_chat_explorer_lib.api.sub_api.content_api import router as content_router
app.include_router(content_router, prefix="/content_item", tags=["content_item"])

########################
# ContentFolders関連
########################
app.include_router(content_router, prefix="/content_folder", tags=["content_folder"])

########################
# SearchRule関連
########################
from ai_chat_explorer_lib.api.sub_api.search_api import router as search_rule_router
app.include_router(search_rule_router, prefix="/search_rule", tags=["search_rule"])

########################
# TagItem関連
########################
from ai_chat_explorer_lib.api.sub_api.tag_item_api import router as tag_item_router
app.include_router(tag_item_router, prefix="/tag_item", tags=["tag_item"])

########################
# ベクトルDB関連
########################
from  vector_search_util.api.api_server import router as vector_db_router
app.include_router(vector_db_router, prefix="/vector_search", tags=["vector_search"])

########################
# ファイル関連
########################
from file_util.api.api_server import router as file_util_router
app.include_router(file_util_router, prefix="/file_util", tags=["file_util"])

########################
# Web関連
########################
from web_search_util.api.api_server import router as web_util_router
app.include_router(web_util_router, prefix="/web_util", tags=["web_util"])

# ping
@app.get('/ping')
async def ping() -> str:
    return "pong"

@app.post('/shutdown')
async def shutdown_server(request: Request) -> None:
    client_host = request.client.host if request.client else None
    if client_host not in {"127.0.0.1", "::1", "localhost"}:
        raise HTTPException(status_code=403, detail="shutdown is only allowed from localhost")

    shutdown_token = os.getenv("API_SHUTDOWN_TOKEN")
    if shutdown_token:
        provided = request.headers.get("x-api-token")
        if provided != shutdown_token:
            raise HTTPException(status_code=403, detail="invalid shutdown token")

    pid = os.getpid()
    os.kill(pid, signal.SIGINT)

async def main(port: int = 5000) -> None:
    """
    - アプリケーション初期化・ルーティング・サーバ起動
    """
    from dotenv import load_dotenv
    load_dotenv()
    # アプリケーション初期化
    """
    アプリケーション初期化時に呼び出される非同期関数。
    DBの初期化・マイグレーションを実施する。
    """
    await MainDBUtil.init(upgrade=True)

    logger.info(f"port={port}")
    root_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @root_app.get("/docs", include_in_schema=False)
    async def _redirect_docs():
        return RedirectResponse(url="/api/docs")

    @root_app.get("/redoc", include_in_schema=False)
    async def _redirect_redoc():
        return RedirectResponse(url="/api/redoc")

    @root_app.get("/openapi.json", include_in_schema=False)
    async def _redirect_openapi():
        return RedirectResponse(url="/api/openapi.json")

    root_app.mount("/api", app)
    uvicorn_config = uvicorn.Config(root_app, host="0.0.0.0", port=int(port))
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == '__main__':
    import asyncio
    import argparse
    parser = argparse.ArgumentParser(description='AI Chat Explorer API Server')
    parser.add_argument('--port', type=int, default=5000, help='Port number to run the server on')
    args = parser.parse_args()
    asyncio.run(main(port=args.port))
