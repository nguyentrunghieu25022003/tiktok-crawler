import aiohttp
from typing import Optional, List, Dict, Iterator

class Place:
    def __init__(self, data: List[Dict], parent: Optional[object] = None) -> None:
        """
        Args:
            data (List[Dict]): Danh sách các entry từ file JSON chứa thông tin POI.
            parent (object, optional): Tham chiếu đến đối tượng TikTokApi (để tạo đối tượng video,…).
        """
        self.data = data
        self.parent = parent
        self.id: Optional[str] = None
        self.name: Optional[str] = None

    def get_id_by_hashtag(self, hashtag: str) -> Optional[str]:
        hashtag = hashtag.lower()
        for entry in self.data:
            # Giả sử mỗi entry có khóa "hashtag" (dưới dạng chuỗi)
            if "hashtag" in entry and entry["hashtag"].lower() == hashtag:
                self.id = entry.get("id")
                self.name = entry.get("name")
                return self.id
        return None

    async def videos(self, hashtag: str, count: int = 30, cursor: int = 0, **kwargs) -> Iterator[object]: # type: ignore
        """
        Lấy video từ API của TikTok cho một địa điểm (POI) dựa trên hashtag.
        Phương thức này sẽ:
          1. Tra cứu trong file JSON (đã load vào đối tượng Place) để lấy được POI id ứng với hashtag.
          2. Tái tạo lại tham số (params) theo định dạng mẫu URL và gọi trực tiếp API thông qua aiohttp.
          3. Duyệt qua danh sách video (danh sách nằm trong key "itemList") và tạo đối tượng video qua parent.video(data=...).

        Args:
            hashtag (str): Hashtag của địa điểm (ví dụ: "hanoi", "tphcm", …).
            count (int): Số lượng video cần lấy.
            cursor (int): Giá trị phân trang (offset). Ví dụ: trang 1 offset = 0, trang 2 offset = count, v.v.

        Yields:
            Mỗi phần tử video được tạo bởi self.parent.video(data=video_data).
        """
        poi_id = self.get_id_by_hashtag(hashtag)
        if not poi_id:
            raise Exception(f"Place ID not found for hashtag '{hashtag}'")

        params = {
            "WebIdLastTime": kwargs.get("WebIdLastTime", 1679299803),
            "aid": 1988,
            "app_language": "vi-VN",
            "app_name": "tiktok_web",
            "browser_language": "en-US",
            "browser_name": "Mozilla",
            "browser_online": "true",
            "browser_platform": "Win32",  # theo mẫu URL mẫu có Win32
            "browser_version": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "channel": "tiktok_web",
            "cookie_enabled": "true",
            "count": count,
            "cursor": cursor,
            "data_collection_enabled": "true",
            # Giả sử device_id được cung cấp trong kwargs hoặc dùng giá trị mặc định
            "device_id": kwargs.get("device_id", "7212537679388788226"),
            "device_platform": "web_pc",
            "focus_state": "true",
            "from_page": "",
            "history_len": 4,
            "is_fullscreen": "false",
            "is_page_visible": "true",
            "language": "vi-VN",
            # Giá trị odinId cố định theo mẫu URL
            "odinId": kwargs.get("odinId", "7030772186080183322"),
            "os": "windows",
            "poiId": poi_id,
            "priority_region": "VN",
            "referer": "",
            "region": "VN",
            "screen_height": 864,
            "screen_width": 1536,
            "tz_name": "Asia/Saigon",
            "user_is_login": "true",
            "webcast_language": "vi-VN"
        }
        
        url = "https://www.tiktok.com/api/poi/item_list/"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error: {response.status}")
                resp = await response.json()

        if resp is None:
            raise Exception("Invalid response from poi/item_list endpoint.")
        
        for video_data in resp.get("itemList", []):
            yield self.parent.video(data=video_data)

    def __repr__(self) -> str:
        return f"Place(id={self.id}, name={self.name})"

    def __str__(self) -> str:
        return self.__repr__()
