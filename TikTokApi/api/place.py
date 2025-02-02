from __future__ import annotations
from ..exceptions import *

from typing import TYPE_CHECKING, ClassVar, Iterator, Optional

if TYPE_CHECKING:
    from ..tiktok import TikTokApi
    from .video import Video

from .hashtag import Hashtag

class Place(Hashtag):
    """
    A TikTok Place.

    This class inherits from Hashtag to fetch the challenge id (which is used to obtain the POI id)
    by calling the challenge/detail endpoint once. Then it calls the challenge/item_list endpoint to
    extract the POI id from a video, and finally uses that POI id to call the poi/item_list endpoint to fetch videos.

    """

    async def info(self, **kwargs) -> dict:
        """
        Override info() to use challenge/detail to fetch POI id.
        """
        info_data = await super().info(**kwargs)
        return info_data
    
    async def videos(self, count=30, cursor=0, **kwargs) -> Iterator[Video]: # type: ignore
        """
        Override videos() to use the following flow:
          1. If self.id is not set, call super().info() to obtain challenge id.
          2. Use challenge id to call challenge/item_list once and extract POI id from one of the videos.
          3. Then, use the POI id to call poi/item_list to fetch videos.

        Args:
            count (int): Number of videos to return.
            cursor (int): Offset for video retrieval.

        Returns:
            async iterator/generator: Yields TikTokApi.video objects.
        """
        
        if getattr(self, "id", None) is None:
            await super().info(**kwargs)
        
        challenge_params = {
            "challengeID": self.id,
            "count": 5,
            "cursor": 30,
        }
        
        challenge_resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/challenge/item_list/",
            params=challenge_params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )
        
        if challenge_resp is None or not challenge_resp.get("itemList"):
            raise InvalidResponseException(challenge_resp, "Failed to fetch data from challenge/item_list.")
        
        videos_list = challenge_resp.get("itemList", [])
        poi_id = None
        for video in videos_list:
            poi_info = video.get("poi", {})
            if poi_info and poi_info.get("id"):
                poi_id = poi_info.get("id")
                break
            
        if not poi_id:
            raise Exception("Failed to extract POI id from challenge/item_list response.")
        
        self.id = poi_id

        found = 0
        while found < count:
            params = {
                "poiId": self.id,
                "count": 30,
                "cursor": cursor,
            }

            resp = await self.parent.make_request(
                url="https://www.tiktok.com/api/poi/item_list/",
                params=params,
                headers=kwargs.get("headers"),
                session_index=kwargs.get("session_index"),
            )
            
            if resp is None:
                raise InvalidResponseException(resp, "TikTok returned an invalid response from poi/item_list.")
            
            for video in resp.get("itemList", []):
                yield self.parent.video(data=video)
                found += 1
            if not resp.get("hasMore", False):
                return
            cursor = resp.get("cursor")

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTokApi.place(id='{getattr(self, 'id', None)}', name='{getattr(self, 'name', None)}')"
