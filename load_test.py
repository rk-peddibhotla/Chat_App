import socketio
import threading
import time

SERVER_URL = "http://127.0.0.1:5000" 
ROOM_CODE = "TEST"  
NUM_USERS = 10
MESSAGES_PER_USER = 20
MESSAGE_INTERVAL = 0.2  

def simulate_user(user_id):
    sio = socketio.Client()
    name = f"user{user_id}"

    @sio.event
    def connect():
        print(f"{name} connected")
        
        sio.emit("join_room_manual", {"name": name, "room": ROOM_CODE})

    @sio.event
    def joined(data):
        print(f"{name} joined room {data['room']}")
        for i in range(MESSAGES_PER_USER):
            msg = f"Hello from {name} #{i}"
            sio.emit("message", {"data": msg})
            time.sleep(MESSAGE_INTERVAL)
        sio.disconnect()

    @sio.event
    def disconnect():
        print(f"{name} disconnected")

    @sio.event
    def error(data):
        print(f"{name} error: {data}")

    sio.connect(SERVER_URL)
    sio.wait()

if __name__ == "__main__":
    threads = []
    for i in range(NUM_USERS):
        t = threading.Thread(target=simulate_user, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("Load test complete")
