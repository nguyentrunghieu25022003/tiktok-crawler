from __future__ import annotations
import random
from ..exceptions import *
from ..helpers import generate_web_search_code
import logging

from typing import TYPE_CHECKING, ClassVar, AsyncIterator, Optional, Dict, Any
from urllib.parse import urlencode, quote
from ..helpers import fetch_odin_id, fetch_logid

if TYPE_CHECKING:
    from ..tiktok import TikTokApi
    from .video import Video

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
            self.search_id = await fetch_logid(
                resp = await self.parent.make_request(
                    url="https://www.tiktok.com/api/search/item/full/",
                    params=params,
                    headers=kwargs.get("headers"),
                    session_index=kwargs.get("session_index"),
                )
            )
            
        print({
            "odin_id": self.odin_id,
            "search_id": self.search_id
        })

        return {
            "odin_id": self.odin_id,
            "search_id": self.search_id
        }
    
    async def videos(self, offset: int = 0, **kwargs) -> AsyncIterator[Video]:
        """
        Trả về một async generator của các video dựa trên kết quả tìm kiếm.
        """
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
        
        # In ra URL hoàn chỉnh để debug
        print(f"Full URL: {full_url}")
        
        resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/search/item/full/",
            params=params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )
        
        if resp is None:
            raise InvalidResponseException(resp, "TikTok returned an invalid response.")
        
        print("Response:", resp)

        # Giả sử key trả về chứa danh sách video là "item_list"
        for video in resp.get("item_list", []):
            print("Video:", video)
            # yield từng đối tượng video được tạo ra qua self.parent.video(...)
            yield self.parent.video(data=video)
    
    def __repr__(self) -> str:
        count = len(self.as_dict.get("item_list", [])) if self.as_dict else 0
        return f"SearchVideo(keyword='{self.keyword}', items={count})"
