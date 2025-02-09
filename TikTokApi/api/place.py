from typing import Optional, List, Dict, Iterator

class Place:
    def __init__(self, data: List[Dict], parent: Optional[object] = None) -> None:
        self.data = data
        self.parent = parent
        self.id: Optional[str] = None
        self.name: Optional[str] = None

    def get_id_by_hashtag(self, hashtag: str) -> Optional[str]:
        hashtag = hashtag.lower()
        for entry in self.data:
            if "hashtag" in entry and entry["hashtag"].lower() == hashtag:
                self.id = entry.get("id")
                self.name = entry.get("name")
                return self.id
        return None

    async def videos(self, hashtag: str, count: int = 30, cursor: int = 0, **kwargs) -> Iterator[object]: # type: ignore
        poi_id = self.get_id_by_hashtag(hashtag)
        if not poi_id:
            raise Exception(f"Place ID not found for hashtag '{hashtag}'")
        
        params = {
            "poiId": poi_id,
            "count": count,
            "cursor": cursor,
        }
        
        resp = await self.parent.make_request(
            url="https://www.tiktok.com/api/poi/item_list/",
            params=params,
            headers=kwargs.get("headers"),
            session_index=kwargs.get("session_index"),
        )
        
        if resp is None:
            raise Exception("Invalid response from poi/item_list endpoint.")
        
        for video_data in resp.get("itemList", []):
            yield self.parent.video(data=video_data)
    
    def __repr__(self) -> str:
        return f"Place(id={self.id}, name={self.name})"

    def __str__(self) -> str:
        return self.__repr__()
