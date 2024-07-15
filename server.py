import os
import uvicorn
from dotenv import load_dotenv
load_dotenv(os.getenv('ENV_PATH', '.env'))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, HTTPException

from dapr.ext.fastapi import DaprApp
from dapr.ext.fastapi import DaprActor

from actors import BannerActor, BannerActorInterface

from models import Banner, UpdateBanner
from dapr.actor import ActorProxy, ActorId

PORT = int(os.getenv('PORT', 30212))
BANNER_IDS = ['lightning', 'sparky']

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('~~ actor startup')
    await actor.register_actor(BannerActor)
    yield
    # Do shutdown cleanup here...

app = FastAPI(title="AirDisplay API", lifespan=lifespan)
dapr_app = DaprApp(app)
actor = DaprActor(app)    

@dapr_app.subscribe(pubsub='pubsub', topic='banner_updated')
def any_event_handler(event_data = Body()):
    print('~~ ON EVENT:', event_data)

@app.get("/")
async def read_root() -> str:
    return 'AirDisplay!'

@app.get("/healthz")
async def healthcheck():
    return "Healthy!"

@app.post("/banner/{id}")
async def get_banner(id: str, update: UpdateBanner):
    if id not in BANNER_IDS:
        raise HTTPException(status_code=400, detail="Invalid banner ID")

    try:
        proxy = ActorProxy.create('BannerActor', ActorId(id), BannerActorInterface)
        banner = await proxy.UpdateState(update.model_dump(exclude_unset=True))
        return banner
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/banners")
async def get_banners() -> list[Banner]:
    banners = []
    for id in BANNER_IDS:
        proxy = ActorProxy.create('BannerActor', ActorId(id), BannerActorInterface)
        banner = await proxy.GetState()
        banners.append(banner)

    return banners

@app.get("/banner/{id}")
async def get_banner(id: str) -> Banner:
    if id not in BANNER_IDS:
        raise HTTPException(status_code=400, detail="Invalid banner ID")
    
    try:
        proxy = ActorProxy.create('BannerActor', ActorId(id), BannerActorInterface)
        banner = await proxy.GetState()
        return banner
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
