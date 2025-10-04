import asyncio
import websockets
import json
import os

# { room_id: { 'peers': [ws1, ws2], 'last_offer': {...} } }
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

                if room not in rooms:
                    rooms[room] = {'peers': [], 'last_offer': None}

                room_data = rooms[room]

                if msg_type == "join":
                    if len(room_data['peers']) >= 2:
                        await websocket.send(json.dumps({"error": "Room is full"}))
                        continue
                    is_first = len(room_data['peers']) == 0
                    room_data['peers'].append(websocket)

                    # Отправить joined
                    await websocket.send(json.dumps({"type": "joined", "is_first": is_first}))

                    # Если это второй участник и есть last_offer — отправить ему offer
                    if not is_first and room_data['last_offer']:
                        await websocket.send(json.dumps(room_data['last_offer']))

                    continue

                # Если это offer — сохранить его
                if msg_type == "offer":
                    room_data['last_offer'] = data

                # Рассылка всем, кроме отправителя
                for peer in room_data['peers']:
                    if peer != websocket and peer.open:
                        await peer.send(message)

            except Exception as e:
                print("Message error:", e)
    finally:
        # Удалить из комнаты
        for room_id, room_data in list(rooms.items()):
            if websocket in room_data['peers']:
                room_data['peers'].remove(websocket)
                if not room_data['peers']:
                    del rooms[room_id]
