from typing import Sequence
import os, sys
from fastapi import FastAPI
import uvicorn

from ai_chat_explorer_lib.db.main_db_util import MainDBUtil

# vector search util
import vector_search_util.api.api_server as vector_db_api

import ai_chat_explorer_lib.log.log_settings as log_settings
logger = log_settings.getLogger(__name__)

app = FastAPI()

########################
# OpenAI Chat関連
########################
import ai_chat_explorer_lib.api.api_server as ai_chat_api
app.mount( "/ai_chat", ai_chat_api.app)

########################
# AutoProcess関連
########################
from ai_chat_explorer_lib.api.sub_api.auto_process_api import app as auto_process_app
app.mount("/auto_process", auto_process_app)

########################
# PromptItem関連
########################
from ai_chat_explorer_lib.api.sub_api.prompt_item_api import app as prompt_item_app
app.mount("/prompt_item", prompt_item_app)


########################
# ContentItem関連
########################
from ai_chat_explorer_lib.api.sub_api.content_api import app as content_item_app
app.mount("/content_item", content_item_app)

########################
# ContentFolders関連
########################
from ai_chat_explorer_lib.api.sub_api.content_api import app as content_item_app

########################
# SearchRule関連
########################
from ai_chat_explorer_lib.api.sub_api.search_api import app as search_rule_app
app.mount("/search_rule", search_rule_app)

########################
# TagItem関連
########################
from ai_chat_explorer_lib.api.sub_api.tag_item_api import app as tag_item_app
app.mount("/tag_item", tag_item_app)

########################
# ベクトルDB関連
########################
import vector_search_util.api.api_server as vector_db_api
app.mount( "/vector_search", vector_db_api.app)

########################
# ファイル関連
########################
import file_util.api.api_server as file_util_api
app.mount( "/file_util", file_util_api.app)

########################
# Web関連
########################
import web_search_util.api.api_server as web_util_api
app.mount( "/web_util", web_util_api.app)

# ping
@app.get('/ping')
async def ping() -> str:
    return "pong"

@app.post('/shutdown')
async def shutdown_server() -> None:
    pid = os.getpid()
    # Ctrl+CでSIGINTを送信してもらう
    os.kill(pid, 2)

async def main(port: int = 5000):
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
    root_app = FastAPI()
    root_app.mount("/api", app)
    uvicorn_config = uvicorn.Config(root_app, host="0.0.0.0", port=int(port))
    server = uvicorn.Server(uvicorn_config)
    await server.serve()


if __name__ == ('__main__'):
    import asyncio
    import argparse
    parser = argparse.ArgumentParser(description='AI Chat Explorer API Server')
    parser.add_argument('--port', type=int, default=5000, help='Port number to run the server on')
    args = parser.parse_args()
    asyncio.run(main(port=args.port))
