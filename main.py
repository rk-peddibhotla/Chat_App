#pip install Flask
#pip install flask-socketio


from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase
from datetime import datetime
from flask_socketio import emit, join_room

app = Flask(__name__)
app.config["SECRET_KEY"]= "secrentkey"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ''.join(random.choices(ascii_uppercase, k=length))
        if code not in rooms:
            return code



@app.route("/", methods=["POST","GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False) 

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": [], "message_count": 0, "peak_users": 0}
        
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        

        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")




@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    rooms[room]["message_count"] += 1
    print(f"[DEBUG] Message count in room {room}: {rooms[room]['message_count']}")
    print(f"{session.get('name')} said: {data['data']}")



@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return 
    
    join_room(room)
    send({"name": name, "message": "has enetered the room", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, to=room)
    rooms[room]["members"] += 1
    if rooms[room]["members"] > rooms[room]["peak_users"]:
        rooms[room]["peak_users"] = rooms[room]["members"]

    print(f"[DEBUG] Peak users in room {room}: {rooms[room]['peak_users']}")
    print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <=0:
            del rooms[room]
        
        else:
            send({"name": name, "message": "has left the room" ,"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, to=room)
        print(f"{name} has left the room {room}")



@socketio.on("request_stats")
def send_room_stats():
    room = session.get("room")
    if room in rooms:
        emit("room_stats", {
            "messages": rooms[room]["message_count"],
            "users": rooms[room]["members"],
            "peak": rooms[room]["peak_users"]
        })




@socketio.on("join_room_manual")
def handle_manual_join(data):
    name = data.get("name")
    room = data.get("room")
    if not name or not room:
        emit("error", {"message": "Name and room required"})
        return
    
    # Store user info in session (optional)
    session["name"] = name
    session["room"] = room

    # Create room if doesn't exist (for test only)
    if room not in rooms:
        rooms[room] = {
            "members": 0,
            "messages": [],
            "message_count": 0,
            "peak_users": 0
        }

    join_room(room)
    rooms[room]["members"] += 1
    if rooms[room]["members"] > rooms[room]["peak_users"]:
        rooms[room]["peak_users"] = rooms[room]["members"]

    emit("joined", {"room": room, "name": name})
    send({"name": name, "message": "has entered the room", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, to=room)
    print(f"{name} manually joined room {room}")


if __name__ == "__main__":
    socketio.run(app, debug=True)

