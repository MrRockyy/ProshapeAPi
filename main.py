from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
from bson import json_util, ObjectId
from datetime import datetime, timedelta
import pytz
import os
def generar_array_fechas():
    fecha_actual = datetime.utcnow().replace(tzinfo=pytz.utc)
    zona_bogota = pytz.timezone('America/Bogota')
    fecha_actual_bogota = fecha_actual.astimezone(zona_bogota)
    fechas_array = []

    def agregar_fecha(fecha):
        fecha_formateada = str(fecha.strftime('%y-%m-%d'))
        fechas_array.append(fecha_formateada)

    for i in range(30, 0, -1):
        fecha = fecha_actual_bogota - timedelta(days=i)
        agregar_fecha(fecha)

    agregar_fecha(fecha_actual_bogota)

    for i in range(1, 30):
        fecha = fecha_actual_bogota + timedelta(days=i)
        agregar_fecha(fecha)

    return fechas_array

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'Cxv24KPcpogXnqgpDAXF' 
jwt = JWTManager(app)
CORS(app)

client = MongoClient("mongodb+srv://proshape:a0A8y0PTVONUd7au@cluster0.navtwdq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['proshape']
users_collection = db['users']
events_collection = db['events']
@app.route('/test', methods=['GEt'])
def test():
      return jsonify({"msg": "puta madre"})
    
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    dateStart = data.get('dateStart')
    date = data.get('date')
    genre = data.get('genre')
    photo = data.get('photo')
    name = data.get('name')
    direction = data.get('direccion')
    description = data.get('description')
    descriptionStatus=data.get('descriptionStatus')
    

    if users_collection.find_one({"username": username}):
        return jsonify({"msg": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"direction":direction,"description":description,"descriptionStatus":descriptionStatus,"dateEndShort":"", "dateEndlong":"", "main3":0,"main2":0,"main1":0,"classes": [], "phone": phone, "dateStart": dateStart, "plan": "", "rol": "user", "date": date, "genre": genre, "photo": photo, "name": name, "username": username, "password": hashed_password})

    return jsonify({"msg": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({"username": username})

    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/events', methods=['GET'])
def events():
    date = request.args.get('date')
    eventos_lista = []

    for evento in events_collection.find({"date": date}):
        # Convert the _id field to a string
        evento['_id'] = str(evento['_id'])
        eventos_lista.append(evento)
    
    eventos_json = json_util.dumps(eventos_lista, default=str)
    return eventos_json

@app.route('/api/events', methods=['POST'])
def eventCreate():
    data = request.get_json()
    username = data.get('username')
    dateEvent = data.get('dateEvent')
    cupo = data.get('cupo')
    name = data.get("name")
    startTime = data.get("startTime")
    endTime = data.get("endTime")
    num = 0
    letter = 0
    type = data.get('type')
    nameEvent = data.get('nameEvent')
    cupoNow = 0

    events_collection.insert_one({
        'username': username,
        "nameTeacher": name,
        'date': dateEvent,
        'cupo': cupo,
        'num': num,
        'letter': letter,
        "startTime": startTime,
        "endTime": endTime,
        'type': type,
        'nameEvent': nameEvent,
        'cupoNow': cupoNow,
        'members': [],
        'WaitList': []
    })
    return jsonify({"msg": "User Event created successfully"}), 201

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/api/join', methods=['POST'])
@jwt_required()
def join():
    event_id = request.args.get('event')
    current_user = get_jwt_identity()
    bogota_tz = pytz.timezone('America/Bogota')
    user_document = users_collection.find_one({"username": current_user})
    
    if (user_document and 
        int(user_document.get("main2", 0)) > 0 and 
        user_document.get("dateEndLong") and 
        datetime.strptime(user_document["dateEndLong"], '%Y-%m-%d').replace(tzinfo=bogota_tz) > datetime.now(bogota_tz)):

        event = events_collection.find_one({"_id": ObjectId(event_id)})

        if not event:
            return jsonify({"msg": "Event not found"}), 404

        if current_user in event['members']:
            events_collection.update_one(
                {"_id": ObjectId(event_id)},
                {"$pull": {"members": current_user}, "$inc": {"cupoNow": -1}}
            )
            users_collection.update_one(
                {"username": current_user},
                {"$inc": {"main1": -1, "main2": 1}}
            )
            if event['WaitList']:
                first_waitlist_user = event['WaitList'].pop(0)
                events_collection.update_one(
                    {"_id": ObjectId(event_id)},
                    {"$push": {"members": first_waitlist_user}, "$set": {"WaitList": event['WaitList']}, "$inc": {"cupoNow": 1}}
                )
                return jsonify({"msg": "User removed from the event and the first user from the waitlist added to members"}), 200
            else:
                return jsonify({"msg": "User removed from the event"}), 200

        elif current_user not in event['members']:
            if int(event['cupoNow']) >= int(event['cupo']):
                events_collection.update_one(
                    {"_id": ObjectId(event_id)},
                    {"$push": {"WaitList": current_user}}
                )
                users_collection.update_one(
                    {"username": current_user},
                    {"$inc": {"main1": 1, "main2": -1}}
                )
                return jsonify({"msg": "Event is full. User added to the waitlist"}), 200
            else:
                events_collection.update_one(
                    {"_id": ObjectId(event_id)},
                    {"$push": {"members": current_user}, "$inc": {"cupoNow": 1}}
                )
                users_collection.update_one(
                    {"username": current_user},
                    {"$inc": {"main1": 1, "main2": -1}}
                )
                return jsonify({"msg": "User added to the event"}), 200

        elif current_user in event['WaitList']:
            events_collection.update_one(
                {"_id": ObjectId(event_id)},
                {"$pull": {"WaitList": current_user}}
            )
            users_collection.update_one(
                {"username": current_user},
                {"$inc": {"main1": -1, "main2": 1}}
            )
            return jsonify({"msg": "User removed from the waitlist"}), 200

    else:
        return jsonify({"msg": "Invalid user or expired membership"}), 400


@app.route('/api/main', methods=['GET'])
@jwt_required()
def main():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"username": current_user}, {"_id": 0})
    if user:
        return json_util.dumps(user), 200
    else:
        return jsonify({"msg": "User not found"}), 404

if __name__ == '__main__':
      app.run(debug=True, port=os.getenv("PORT", default=5000))