from __future__ import annotations
import random
from ..exceptions import *
from ..helpers import generate_web_search_code
import logging

from typing import TYPE_CHECKING, ClassVar, Iterator, Optional

if TYPE_CHECKING:
    from ..tiktok import TikTokApi
    from .video import Video

from urllib.parse import urlencode, quote
from typing import Optional, Dict, Any, Iterator
from ..helpers import fetch_odin_id, fetch_logid

class SearchVideo:
    parent: ClassVar[TikTokApi]
    keyword: str
    odin_id: Optional[str]
    search_id: Optional[str]
    as_dict: Dict[str, Any]

    def __init__(self, keyword: str, parent: Optional[Any] = None, data: Optional[Dict[str, Any]] = None) -> None:
        if not keyword:
            raise TypeError("You must provide a keyword.")
        self.keyword = keyword
        self.odin_id = None
        self.search_id = None
        self.as_dict = data or {}
        self.parent = parent
        
        if not hasattr(self, 'logger'):
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    async def info(self, **kwargs) -> Dict[str, Any]:
        if not self.odin_id:
            self.odin_id = await fetch_odin_id(self.keyword)
            
        web_search_code = generate_web_search_code(keyword=self.keyword)
            
        params = {
            "keyword": self.keyword,
            "offset": 0,
            "web_search_code": web_search_code,
            "odinId": self.odin_id,
            "msToken": kwargs.get("ms_token"),
        }
        
        if not self.search_id:
            self.search_id = await fetch_logid(resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/search/item/full/",
            params=params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        ));

        return {
            "odin_id": self.odin_id,
            "search_id": self.search_id
        }
    
    async def videos(self, offset = 0, **kwargs) -> Iterator[Video]: # type: ignore
        web_search_code = generate_web_search_code(keyword=self.keyword)
        
        params = {
            "keyword": self.keyword,
            "offset": offset,
            "web_search_code": web_search_code,
            "odinId": self.odin_id,
            "search_id": self.search_id,
        }
        
        base_url = "https://www.tiktok.com/api/search/item/full/"
        full_url = f"{base_url}?{urlencode(params, safe='=', quote_via=quote)}"
        
        # In ra URL hoàn chỉnh
        print(f"Full URL: {full_url}")
        
        resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/search/item/full/",
            params=params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )
        
        if resp is None:
            raise InvalidResponseException(resp, "TikTok returned an invalid response.")
        
        print("Res", resp)

        for video in resp.get("item_list", []):
            yield self.parent.video(data=video)
            found += 1
    
    def __repr__(self) -> str:
        count = len(self.as_dict.get("item_list", [])) if self.as_dict else 0
        return f"SearchVideo(keyword='{self.keyword}', items={count})"