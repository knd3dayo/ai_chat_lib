import json
from typing import Any
from web_search_mcp.web_modules.web_util import WebUtil
from ai_chat_lib.api_modules.ai_app_data import AIAppData
class WebUtilAPI:

    @classmethod
    async def extract_webpage_api(cls,request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # web_requestを取得
        request = AIAppData.get_web_request_objects(request_dict)

        url = request.get("url", None)
        if url is None:
            raise ValueError("URL is not set in the web_request object.")
        text, urls = await WebUtil.extract_webpage(url)
        result: dict[str, Any] = {}
        result["output"] = text
        result["urls"] = urls
        result["base_url"] = url
        return result
    