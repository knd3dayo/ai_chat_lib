from typing import Any, Annotated, Union, Callable
from autogen_core.code_executor import ImportFromModule
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import BaseChatMessage
import asyncio
from playwright.async_api import async_playwright

# Edge用のWebドライバーを毎回ダウンロードしなくてもよいようにグローバル変数化
edge_driver = None # type: ignore
async def extract_webpage(url: Annotated[str, "URL of the web page to extract text and links from"]) -> Annotated[tuple[str, list[tuple[str, str]]], "Page text, list of links (href attribute and link text from <a> tags)"]:
    """
    This function extracts text and links from the specified URL of a web page.
    """
    async with async_playwright() as p:
        # EdgeのWebドライバーを取得
        edge_driver = await p.chromium.launch(headless=True, executable_path="msedge")
        browser = edge_driver
        page = await browser.new_page()
        await page.goto(url)
        page_html = await page.content()
        await page.close()


    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_html, "html.parser")
    text = soup.get_text()
    # Retrieve href attribute and text from <a> tags
    urls: list[tuple[str, str]] = [(a.get("href"), a.get_text()) for a in soup.find_all("a")] # type: ignore
    return text, urls
