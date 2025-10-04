# server.py
import asyncio
import websockets
import json
import os
import signal

# Хранилище комнат: { room_id: [websocket1, websocket2] }
rooms = {}

async def handler(websocket, path):
    print("Новое соединение")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                room = data.get("room")
                msg_type = data.get("type")

                if not room:
                    await websocket.send(json.dumps({"error": "room is required"}))
                    continue

                # Присоединение к комнате
                if msg_type == "join":
                    if room not in rooms:
                        rooms[room] = []
                    if len(rooms[room]) >= 2:
                        await websocket.send(json.dumps({"error": "Room is full (max 2 users)"}))
                        continue
                    rooms[room].append(websocket)
                    print(f"Пользователь присоединился к комнате {room}")
                    continue

                # Рассылка сообщения другому участнику
                peers = rooms.get(room, [])
                for peer in peers:
                    if peer != websocket and peer.open:
                        await peer.send(message)

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
            except Exception as e:
                print("Ошибка обработки:", e)

    except websockets.exceptions.ConnectionClosed:
        print("Соединение закрыто")
    finally:
        # Удалить websocket из всех комнат
        for room in list(rooms.keys()):
            if websocket in rooms[room]:
                rooms[room].remove(websocket)
                print(f"Пользователь покинул комнату {room}")
                if not rooms[room]:
                    del rooms[room]

# Graceful shutdown
def shutdown():
    print("Завершение работы...")
    for room in list(rooms.keys()):
        del rooms[room]

# Запуск сервера
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    print(f"Сервер запускается на порту {port}...")

    # Регистрация обработчика завершения
    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    start_server = websockets.serve(handler, "0.0.0.0", port)
    server = loop.run_until_complete(start_server)

    try:
        loop.run_until_complete(stop)
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        shutdown()