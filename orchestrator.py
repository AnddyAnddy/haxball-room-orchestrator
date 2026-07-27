import asyncio
import json
import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis

import config

_debounce_task: asyncio.Task | None = None


async def _debounced_sync():
    await asyncio.sleep(config.DEBOUNCE_SECONDS)
    await sync_discord_message()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

r = Redis(host="redis", port=6379, decode_responses=True)

WEBHOOK_URL = os.environ["ORCHESTRATOR_WEBHOOK_URL"]
MSG_ID_KEY = "orchestrator:message_id"
ROOM_KEY = "orchestrator:rooms"


class RoomEvent(BaseModel):
    room_link: str
    room_name: str
    players: int
    max_players: int


def build_embed():
    rooms = r.hgetall(ROOM_KEY)
    lines = []
    for room_name in sorted(rooms.keys()):
        data = json.loads(rooms[room_name])
        lines.append(f"{data['room_name']} {data['room_link']} [{data['players']}/{data['max_players']}]")
    description = "\n".join(lines) if lines else "No rooms online."
    return {"embeds": [{"title": config.title, "description": description, "color": config.color}]}


async def sync_discord_message():
    payload = build_embed()
    msg_id = r.get(MSG_ID_KEY)

    async with httpx.AsyncClient() as client:
        if msg_id:
            resp = await client.patch(f"{WEBHOOK_URL}/messages/{msg_id}", json=payload)
            if resp.status_code == 404:
                msg_id = None

        if not msg_id:
            resp = await client.post(f"{WEBHOOK_URL}?wait=true", json=payload)
            r.set(MSG_ID_KEY, resp.json()["id"])


@app.post("/event")
async def receive_event(event: RoomEvent):
    global _debounce_task
    r.hset(ROOM_KEY, event.room_name, json.dumps(event.dict()))

    if _debounce_task and not _debounce_task.done():
        _debounce_task.cancel()

    _debounce_task = asyncio.create_task(_debounced_sync())
    return {"ok": True}
