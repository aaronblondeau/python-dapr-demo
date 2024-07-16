import os
from dotenv import load_dotenv
load_dotenv(os.getenv('ENV_PATH', '.env'))

import uvicorn
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocketState
from dapr.ext.fastapi import DaprApp
from dapr.ext.fastapi import DaprActor
from actors import BannerActor, BannerActorInterface
from models import Banner, UpdateBanner
from dapr.actor import ActorProxy, ActorId

# This port must match what is used in the dapr run --app-id argument:
PORT = int(os.getenv('PORT', 30212))

# For simplicity only have two hardcoded banner ids
BANNER_IDS = ['lightning', 'sparky']

# Register actor when fastapi starts up
@asynccontextmanager
async def lifespan(app: FastAPI):
    print('~~ actor startup')
    await actor.register_actor(BannerActor)
    yield
    # Do shutdown cleanup here...

# Create fastapi and register dapr, and actors
app = FastAPI(title="AirDisplay API", lifespan=lifespan)
dapr_app = DaprApp(app)
actor = DaprActor(app)

subscribers: list[WebSocket] = []

# The fact that the python dapr sdk only allows you to subscribe to events with a decorator is not ideal.
# We have to subscribe to everything and then distribute on our own...
@dapr_app.subscribe(pubsub='pubsub', topic='banner_updated')
async def ws_events(event_data = Body()):
    print('~~ ON EVENT:', event_data)
    for subscriber in subscribers:
        try:
            await subscriber.send_text(json.dumps(event_data['data']))
        except Exception as e:
            print(e)
            # remove websocket on failed send since it is probably closed
            subscribers.remove(subscriber)

# Dapr hits this to see if your service is running
@app.get("/healthz")
async def healthcheck():
    return "Healthy!"

# Update a specific banner
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

# List all banners
@app.get("/banners")
async def get_banners() -> list[Banner]:
    banners = []
    for id in BANNER_IDS:
        proxy = ActorProxy.create('BannerActor', ActorId(id), BannerActorInterface)
        banner = await proxy.GetState()
        banners.append(banner)

    return banners

# Get a specific banner
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
    
# Provide a websocket to stream updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    subscribers.append(websocket)
    print('~~ Now I have', len(subscribers), 'subscribers')
    # There has to be a better way to do this.
    # Maybe with an asyncio task?
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Websocket incoming text was: {data}")

# Serve the UI
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
