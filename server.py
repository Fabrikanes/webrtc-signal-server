import asyncio
import websockets
import json
import os

rooms = {}

async def handler(websocket, path):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                room = data.get("room")
                msg_type = data.get("type")

                if not room:
                    await websocket.send(json.dumps({"error": "room is required"}))
                    continue

                if msg_type == "join":
                    if room not in rooms:
                        rooms[room] = []
                    if len(rooms[room]) >= 2:
                        await websocket.send(json.dumps({"error": "Room is full"}))
                        continue
                    is_first = len(rooms[room]) == 0
                    rooms[room].append(websocket)
                    print(f"Отправка joined: is_first={is_first}")
                    await websocket.send(json.dumps({"type": "joined", "is_first": is_first}))
                    continue

                # Рассылка другому участнику
                peers = rooms.get(room, [])
                for peer in peers:
                    if peer != websocket and peer.open:
                        await peer.send(message)
            except Exception as e:
                print("Message error:", e)
    finally:
        for room in list(rooms.keys()):
            if websocket in rooms[room]:
                rooms[room].remove(websocket)
                if not rooms[room]:
                    del rooms[room]

async def main():
    port = int(os.environ.get("PORT", 10000))
    print(f"Сервер запускается на порту {port}...")
    server = await websockets.serve(handler, "0.0.0.0", port)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

