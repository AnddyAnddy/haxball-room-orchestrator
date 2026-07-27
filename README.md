# HaxBall Rooms Orchestrator

Aggregates room status from multiple HaxBall headless rooms into a single, self-updating Discord message.

## Setup

1. Create a `.env` file next to `docker-compose.yml`:

```
ORCHESTRATOR_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/xxxxx
```

2. Start the stack:

```bash
docker compose up -d --build
```

The orchestrator listens on port `8000`.

## Sending events from your room scripts (JS)

### With async/await
```javascript
const ORCHESTRATOR_URL = "http://localhost:8000/event";

async function notifyOrchestrator(room, roomLink, roomName, maxPlayers) {
    try {
        await fetch(ORCHESTRATOR_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                room_link: roomLink,
                room_name: roomName,
                players: room.getPlayerList().length,
                max_players: maxPlayers,
            }),
        });
    } catch (err) {
        console.error("Failed to notify orchestrator:", err);
    }
}

room.onPlayerJoin = (player) => notifyOrchestrator(room, "https://www.haxball.com/play?c=abc123", "Room 1", 10);
room.onPlayerLeave = (player) => notifyOrchestrator(room, "https://www.haxball.com/play?c=abc123", "Room 1", 10);
```

### With promises
```javascript
const ORCHESTRATOR_URL = "http://localhost:8000/event";

function notifyOrchestrator(room, roomLink, roomName, maxPlayers) {
    fetch(ORCHESTRATOR_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            room_link: roomLink,
            room_name: roomName,
            players: room.getPlayerList().length,
            max_players: maxPlayers,
        }),
    }).catch((err) => {
        console.error("Failed to notify orchestrator:", err);
    });
}

room.onPlayerJoin = (player) => notifyOrchestrator(room, "https://www.haxball.com/play?c=abc123", "Room 1", 10);
room.onPlayerLeave = (player) => notifyOrchestrator(room, "https://www.haxball.com/play?c=abc123", "Room 1", 10);
```

## Testing with curl

Linux/macOS:

```bash
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"room_link": "https://www.haxball.com/play?c=abc123", "room_name": "Room 1", "players": 4, "max_players": 10}'
```

Windows (PowerShell):

```powershell
curl.exe -X POST http://localhost:8000/event `
  -H "Content-Type: application/json" `
  -d '{\"room_link\": \"https://www.haxball.com/play?c=abc123\", \"room_name\": \"Room 1\", \"players\": 4, \"max_players\": 10}'
```

## Notes

- Rooms are unique by `room_name`. Sending an event with an existing room name updates that room's entry.
- The Discord message is edited in place; it's only created once and reused afterward.

## Clearing Redis

```bash
docker compose exec redis redis-cli FLUSHALL
```