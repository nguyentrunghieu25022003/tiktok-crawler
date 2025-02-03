from __future__ import annotations
from ..exceptions import *

from typing import TYPE_CHECKING, ClassVar, Iterator, Optional

if TYPE_CHECKING:
    from ..tiktok import TikTokApi
    from .video import Video


class Hashtag:
    """
    A TikTok Hashtag/Challenge.

    Example Usage
        .. code-block:: python

            hashtag = api.hashtag(name='funny')
            async for video in hashtag.videos():
                print(video.id)
    """

    parent: ClassVar[TikTokApi]

    id: Optional[str]
    """The ID of the hashtag"""
    name: Optional[str]
    """The name of the hashtag (omiting the #)"""
    as_dict: dict
    """The raw data associated with this hashtag."""

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        data: Optional[dict] = None,
    ):
        """
        You must provide the name or id of the hashtag.
        """

        if name is not None:
            self.name = name
        if id is not None:
            self.id = id

        if data is not None:
            self.as_dict = data
            self.__extract_from_data()

    async def info(self, **kwargs) -> dict:
        """
        Returns all information sent by TikTok related to this hashtag.

        Example Usage
            .. code-block:: python

                hashtag = api.hashtag(name='funny')
                hashtag_data = await hashtag.info()
        """
        if not self.name:
            raise TypeError(
                "You must provide the name when creating this class to use this method."
            )

        url_params = {
            "challengeName": self.name,
            "msToken": kwargs.get("ms_token"),
        }

        resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/challenge/detail/",
            params=url_params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )

        if resp is None:
            raise InvalidResponseException(resp, "TikTok returned an invalid response.")

        self.as_dict = resp
        self.__extract_from_data()
        return resp

    async def videos(self, count: int = 30, page: int = 1, **kwargs) -> Iterator[Video]:  # type: ignore
        """
        Returns TikTok videos that have this hashtag in the caption,
        sử dụng phương pháp phân trang đơn giản theo số trang.

        Args:
            count (int): Số lượng video cần lấy.
            page (int): Số trang, trang 1 có cursor là 0, trang 2 cursor là 30, trang 3 là 60, v.v.
        **kwargs: Các tham số bổ sung (ví dụ ms_token, headers, session_index).

        Returns:
            async iterator/generator: Yields TikTokApi.video objects.

        Example Usage:
            .. code-block:: python

                async for video in api.hashtag(name='funny').videos(page=2, count=30, ms_token="your_ms_token"):
                    print(video.id)
        """
        if getattr(self, "id", None) is None:
            await self.info(**kwargs)
    
        cursor = (page - 1) * 30

        found = 0
        params = {
            "challengeID": self.id,
            "count": count,
            "cursor": cursor,
        }

        resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/challenge/item_list/",
            params=params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )

        if resp is None:
            raise InvalidResponseException(resp, "TikTok returned an invalid response.")

        for video in resp.get("itemList", []):
            yield self.parent.video(data=video)
            found += 1

        # Optionally, nếu bạn muốn trả về cursor kế tiếp để client biết trang tiếp theo,
        # bạn có thể bổ sung vào response hoặc log ra.
        next_cursor = resp.get("cursor")
        print(f"Calculated cursor for page {page}: {cursor}, next_cursor from API: {next_cursor}")


    def __extract_from_data(self):
        data = self.as_dict
        keys = data.keys()

        if "title" in keys:
            self.id = data["id"]
            self.name = data["title"]

        if "challengeInfo" in keys:
            if "challenge" in data["challengeInfo"]:
                self.id = data["challengeInfo"]["challenge"]["id"]
                self.name = data["challengeInfo"]["challenge"]["title"]
                self.split_name = data["challengeInfo"]["challenge"].get("splitTitle")

            if "stats" in data["challengeInfo"]:
                self.stats = data["challengeInfo"]["stats"]

        id = getattr(self, "id", None)
        name = getattr(self, "name", None)
        if None in (id, name):
            Hashtag.parent.logger.error(
                f"Failed to create Hashtag with data: {data}\nwhich has keys {data.keys()}"
            )

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"TikTokApi.hashtag(id='{getattr(self, 'id', None)}', name='{getattr(self, 'name', None)}')"
