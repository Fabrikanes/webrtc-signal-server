# server.py
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
                if not room:
                    await websocket.send(json.dumps({"error": "room is required"}))
                    continue

                if data.get("type") == "join":
                    if room not in rooms:
                        rooms[room] = []
                    if len(rooms[room]) >= 2:
                        await websocket.send(json.dumps({"error": "Room is full"}))
                        continue
                    rooms[room].append(websocket)
                    continue

                # Пересылка другому участнику
                for peer in rooms.get(room, []):
                    if peer != websocket and peer.open:
                        await peer.send(message)
            except Exception as e:
                print("Message error:", e)
    finally:
        # Удалить из комнат
        for room in list(rooms.keys()):
            if websocket in rooms[room]:
                rooms[room].remove(websocket)
                if not rooms[room]:
                    del rooms[room]

async def main():
    port = int(os.environ.get("PORT", 10000))
    print(f"Сервер запускается на порту {port}...")
    server = await websockets.serve(handler, "0.0.0.0", port)
    await server.wait_closed()  # Блокирует выполнение до завершения сервера

if __name__ == "__main__":
    asyncio.run(main())
