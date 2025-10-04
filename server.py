# server.py
from flask import Flask
from flask_sock import Sock
import json
import os

app = Flask(__name__)
sock = Sock(app)

# { room: { 'peers': [ws1, ws2], 'last_offer': {...} } }
rooms = {}

@sock.route('/ws')
def websocket_handler(ws):
    try:
        while True:
            message = ws.receive()
            if not message:
                break
            data = json.loads(message)
            room = data.get("room")
            msg_type = data.get("type")

            if not room:
                ws.send(json.dumps({"error": "room is required"}))
                continue

            if room not in rooms:
                rooms[room] = {'peers': [], 'last_offer': None}

            room_data = rooms[room]

            if msg_type == "join":
                if len(room_data['peers']) >= 2:
                    ws.send(json.dumps({"error": "Room is full"}))
                    continue
                is_first = len(room_data['peers']) == 0
                room_data['peers'].append(ws)
                ws.send(json.dumps({"type": "joined", "is_first": is_first}))
                # Отправить last_offer новому участнику
                if not is_first and room_data['last_offer']:
                    ws.send(json.dumps(room_data['last_offer']))
                continue

            # Сохранить offer
            if msg_type == "offer":
                room_data['last_offer'] = data

            # Рассылка другим
            for peer in room_data['peers']:
                if peer != ws:
                    try:
                        peer.send(message)
                    except:
                        pass  # игнорировать закрытые соединения

    except Exception as e:
        print("WS error:", e)
    finally:
        # Удалить из комнаты
        for room_id, room_data in list(rooms.items()):
            if ws in room_data['peers']:
                room_data['peers'].remove(ws)
                if not room_data['peers']:
                    del rooms[room_id]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
