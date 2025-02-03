import os
import asyncio

if os.name == "nt":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from TikTokApi.tiktok import TikTokApi
import uvicorn

app = FastAPI()

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
    
@app.get("/places/{place}")
async def get_videos(place: str, count: int = 1000):
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
        async for video in api.place(name=place).videos(count=count):
            videos.append(video.as_dict)
            
        await api.stop_playwright()

        return { "videos": videos, "total": len(videos) }

    except Exception as e:
        import traceback
        error_message = traceback.format_exc()
        return {"error": str(e), "traceback": error_message}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000)