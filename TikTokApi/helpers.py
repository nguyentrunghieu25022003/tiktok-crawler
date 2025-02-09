from typing import Any, Dict
from .exceptions import *

import aiohttp # type: ignore
import re
import requests
import random
import json
import urllib
from urllib.parse import quote

def extract_video_id_from_url(url, headers={}, proxy=None):
    url = requests.head(
        url=url, allow_redirects=True, headers=headers, proxies=proxy
    ).url
    if "@" in url and "/video/" in url:
        return url.split("/video/")[1].split("?")[0]
    else:
        raise TypeError(
            "URL format not supported. Below is an example of a supported url.\n"
            "https://www.tiktok.com/@therock/video/6829267836783971589"
        )


def random_choice(choices: list):
    """Return a random choice from a list, or None if the list is empty"""
    if choices is None or len(choices) == 0:
        return None
    return random.choice(choices)

def requests_cookie_to_playwright_cookie(req_c):
    c = {
        'name': req_c.name,
        'value': req_c.value,
        'domain': req_c.domain,
        'path': req_c.path,
        'secure': req_c.secure
    }
    if req_c.expires:
        c['expires'] = req_c.expires
    return c



def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON file ({file_path}): {e}")
        raise

def generate_web_search_code(keyword):
    search_params = {
        "tiktok": {
            "client_params_x": {
                "search_engine": {
                    "ies_mt_user_live_video_card_use_libra": 1,
                    "mt_search_general_user_live_card": 1
                }
            },
            "search_server": {}
        }
    }

    search_params["tiktok"]["client_params_x"]["search_engine"]["keyword"] = keyword

    web_search_code = json.dumps(search_params)

    return urllib.parse.quote(web_search_code)

async def fetch_odin_id(keyword: str) -> str:
    search_url = f"https://www.tiktok.com/search/video?q={quote(keyword)}"
    async with aiohttp.ClientSession() as session:
        async with session.get(search_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch search page for keyword '{keyword}', status: {response.status}")
            html = await response.text()
            match = re.search(
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
                html,
                re.DOTALL
            )
            if match:
                json_text = match.group(1).strip()
                try:
                    data = json.loads(json_text)
                    odin_id = data.get("__DEFAULT_SCOPE__", {}) \
                                  .get("webapp.app-context", {}) \
                                  .get("odinId")
                    if odin_id:
                        return odin_id
                except json.JSONDecodeError:
                    raise Exception("Failed to parse JSON for odinId")
            raise Exception("odinId not found in the search page.")

async def fetch_logid(resp: Dict[str, Any]) -> str:
    # Giả sử response chứa header hoặc field "logid" để lấy search id
    # Ví dụ: từ response['extra']['logid']
    logid = resp.get("extra", {}).get("logid")
    if not logid:
        raise Exception("Search ID not found in policy notice response.")
    return logid
