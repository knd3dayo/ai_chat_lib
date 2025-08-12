from typing import Any, Union
from typing import Annotated
import json
from playwright.async_api import async_playwright
from ai_chat_lib.file_modules.file_util import FileUtil

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)


class WebUtil:
    web_request_name = "web_request"
    @classmethod
    def get_web_request_objects(cls, request_dict: dict) -> dict:
        '''
        {"context": {"web_request": {}}}の形式で渡される
        '''
        # contextを取得
        from typing import Optional
        request: Optional[dict] = request_dict.get(cls.web_request_name, None)
        if not request:
            raise ValueError("request is not set.")
        return request
    
    @classmethod
    async def extract_webpage_api(cls,request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)
        # web_requestを取得
        request = WebUtil.get_web_request_objects(request_dict)

        url = request.get("url", None)
        if url is None:
            raise ValueError("URL is not set in the web_request object.")
        text, urls = await WebUtil.extract_webpage(url)
        result: dict[str, Any] = {}
        result["output"] = text
        result["urls"] = urls
        return result

    @classmethod
    async def extract_webpage(cls, url: Annotated[str, "URL of the web page to extract text and links from"]) -> Annotated[tuple[str, list[tuple[str, str]]], "Page text, list of links (href attribute and link text from <a> tags)"]:
        """
        This function extracts text and links from the specified URL of a web page.
        """
        async with async_playwright() as p:
            # EdgeのWebドライバーを取得
            browser = await p.chromium.launch(headless=True, channel="msedge")
            page = await browser.new_page()
            await page.goto(url)
            page_html = await page.content()
            await browser.close()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_html, "html.parser")
        text = soup.get_text()
        sanitized_text = FileUtil.sanitize_text(text)
        # Retrieve href attribute and text from <a> tags
        urls: list[tuple[str, str]] = [(a.get("href"), a.get_text()) for a in soup.find_all("a")] # type: ignore
        return sanitized_text, urls

