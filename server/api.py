import os
import asyncio

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from TikTokApi.tiktok import TikTokApi
import uvicorn
from TikTokApi.helpers import load_json

app = FastAPI()

current_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(current_dir, "..", "poi_ids.json")

try:
    poi_data = load_json(json_path)
except Exception as e:

    poi_data = {}

@app.get("/")
async def root():
    return { "message": "TikTok API running..." }

@app.get("/hashtag/{hashtag}")
async def get_videos(hashtag: str, count: int = 30, page: int = 1):
    try:
        api = TikTokApi()
        
        await api.start_playwright()
        
        await api.create_sessions(
            num_sessions=1, 
            sleep_after=3, 
            browser="chromium",
            headless=False
        )

        videos = []
        async for video in api.hashtag(name=hashtag).videos(count=count, page=page):
            videos.append(video.as_dict)
            
        await api.stop_playwright()

        return { "videos": videos, "total": len(videos) }

    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        return { "error": str(e), "traceback": error_message }
    
@app.get("/place/{hashtag}")
async def get_videos(hashtag: str, count: int = 30, page: int = 1):
    try:
        api = TikTokApi()
        await api.start_playwright()
        await api.create_sessions(
            num_sessions=1, 
            sleep_after=3, 
            browser="chromium",
            headless=True
        )
        
        place_instance = api.place(data=poi_data, parent=api)

        videos = []
        async for video in place_instance.videos(hashtag=hashtag, count=count, cursor=(page-1)*count):
            videos.append(video.as_dict)
            
        await api.stop_playwright()

        return { "videos": videos, "total": len(videos) }

    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        return { "error": str(e), "traceback": error_message }
    
@app.get("/search")
async def get_videos(keyword: str, offset: int = 0):
    try:
        api = TikTokApi()
        await api.start_playwright()
        await api.create_sessions(
            num_sessions=1, 
            sleep_after=3, 
            browser="chromium",
            headless=False
        )
        
        search_video = api.searchVideo(keyword=keyword, parent=api)
        info = await search_video.info()

        api.logger.info(f"Retrieved info: {info}")

        if 'odin_id' in info and 'search_id' in info:
            api.logger.info(f"Retrieved odin_id: {info['odin_id']} and search_id: {info['search_id']}")

            videos = []
            async for video in search_video.videos(offset=offset):
                videos.append(video.as_dict)

            await api.stop_playwright()

            return { "odin_id": info['odin_id'], "search_id": info['search_id'], "videos": videos, "total": len(videos) }
        else:
            return { "error": "Missing odin_id or search_id in the response" }

    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        return { "error": str(e), "traceback": error_message }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)