# server.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import os

app = FastAPI()

# { room: { 'peers': [ws1, ws2], 'last_offer': {...} } }
rooms = {}

@app.get("/")
async def root():
    return {"status": "WebRTC Signal Server is running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_room = None
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            room = msg.get("room")
            msg_type = msg.get("type")

            if not room:
                await websocket.send_text(json.dumps({"error": "room is required"}))
                continue

            if room not in rooms:
                rooms[room] = {'peers': [], 'last_offer': None}

            room_data = rooms[room]

            if msg_type == "join":
                if len(room_data['peers']) >= 2:
                    await websocket.send_text(json.dumps({"error": "Room is full"}))
                    continue
                is_first = len(room_data['peers']) == 0
                room_data['peers'].append(websocket)
                current_room = room
                await websocket.send_text(json.dumps({"type": "joined", "is_first": is_first}))
                if not is_first and room_data['last_offer']:
                    await websocket.send_text(json.dumps(room_data['last_offer']))
                continue

            if msg_type == "offer":
                room_data['last_offer'] = msg

            # Рассылка другим
            for peer in room_data['peers']:
                if peer != websocket:
                    try:
                        await peer.send_text(data)
                    except:
                        pass

    except WebSocketDisconnect:
        pass
    finally:
        if current_room and current_room in rooms:
            room_data = rooms[current_room]
            if websocket in room_data['peers']:
                room_data['peers'].remove(websocket)
            # Удаляем комнату ТОЛЬКО если в ней никого не осталось
            if len(room_data['peers']) == 0:
                del rooms[current_room]
                print(f"Комната {current_room} удалена (пуста)")


