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

client = MongoClient("mongodb+srv://proshape:a0A8y0PTVONUd7au@cluster0.navtwdq.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true")
db = client['proshape']
users_collection = db['users']
types_collection = db['types']
events_collection = db['events']
comprobantes_collection = db['comprobantes']

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"msg": "puta madre"})

@app.route('/api/update_user', methods=['PUT'])
@jwt_required()
def update_user():
    current_user = get_jwt_identity()
    data = request.get_json()

    update_fields = {field: data[field] for field in [
        "direction", "description", "descriptionStatus", "msg", "notes", "nameShort",
        "dateEndShort", "dateEndlong", "main3", "main2", "main1", "classes",
        "phone", "dateStart", "plan", "rol", "date", "genre", "photo", "name", "username", "typeDocument"
    ] if field in data}

    if update_fields:
        users_collection.update_one({"username": current_user}, {"$set": update_fields})
        return jsonify({"msg": "User updated successfully"}), 200
    else:
        return jsonify({"msg": "No fields to update"}), 400

@app.route('/api/comprobante', methods=['POST'])
@jwt_required()
def comprobante():
    current_user = get_jwt_identity()
    data = request.get_json()
    photo = data.get("photo")
    date = data.get("date")
    name = data.get("name")
    profilePhoto = data.get("profilePhoto")
    comprobantes_collection.insert_one({"name": name, "profilePhoto": profilePhoto, "photo": photo, "username": current_user, "date": date, "status": False})

    return jsonify({"msg": "Comprobante created successfully"}), 201

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    typeDocument = data.get('typeDocument')
    dateStart = data.get('dateStart')
    date = data.get('date')
    genre = data.get('genre')
    photo = data.get('photo')
    name = data.get('name')
    direction = data.get('direccion')
    description = data.get('description')
    descriptionStatus = data.get('descriptionStatus')

    if users_collection.find_one({"username": username}):
        return jsonify({"msg": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "typeDocument": typeDocument, "direction": direction, "description": description, "descriptionStatus": descriptionStatus, "msg": "", "notes": "", "nameShort": "",
        "dateEndShort": "", "dateEndlong": "", "main3": 0, "main2": 0, "main1": 0, "classes": [], "phone": phone, "dateStart": dateStart, "plan": "", "rol": "user", "date": date, 
        "genre": genre, "photo": photo, "name": name, "username": username, "password": hashed_password
    })

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
@app.route('/api/update_password', methods=['PUT'])
@jwt_required()
def update_password():
    current_user = get_jwt_identity()
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    # Busca el usuario actual en la base de datos
    user = users_collection.find_one({"username": current_user})

    if user and check_password_hash(user['password'], old_password):
        # Genera el hash de la nueva contraseña
        hashed_new_password = generate_password_hash(new_password)
        
        # Actualiza la contraseña en la base de datos
        users_collection.update_one({"username": current_user}, {"$set": {"password": hashed_new_password}})
        return jsonify({"msg": "Password updated successfully"}), 200
    else:
        return jsonify({"msg": "Old password is incorrect"}), 400
@app.route('/api/user/update', methods=['PUT'])
@jwt_required()
def update():
    data = request.get_json()
    current_user = data["username"]
    update_fields = {field: data[field] for field in [
        "direction", "description", "descriptionStatus", "msg", "notes", "nameShort",
        "dateEndShort", "dateEndlong", "main3", "main2", "main1", "classes",
        "phone", "dateStart", "plan", "rol", "date", "genre", "photo", "name", "username", "typeDocument"
    ] if field in data}

    if update_fields:
        users_collection.update_one({"username": current_user}, {"$set": update_fields})
        return jsonify({"msg": "User updated successfully"}), 200
    else:
        return jsonify({"msg": "No fields to update"}), 400

@app.route('/api/users', methods=['GET'])
def get_users():
    users = users_collection.find({}, {"_id": 0})
    return jsonify([user for user in users]), 200

@app.route('/api/types', methods=['POST'])
def types():
    data = request.get_json()
    photo = data.get("photo")
    description = data.get("description")
    name = data.get("name")
    types_collection.insert_one({"photo": photo, "description": description, "name": name})

    return jsonify({"msg": "Type created successfully"}), 201

@app.route('/api/types/names', methods=['GET'])
def get_type_names():
    types = types_collection.find({}, {"name": 1, "_id": 0})
    names = [type_['name'] for type_ in types]
    return jsonify({"types": names}), 200

@app.route('/api/entrenadores/names', methods=['GET'])
def get_entrenadores_names():
    types = users_collection.find({"rol": "2"}, {"name": 1, "_id": 0})
    names = [type_['name'] for type_ in types]
    return jsonify({"names": names}), 200

@app.route('/api/events', methods=['POST'])
def eventCreate():
    data = request.get_json()
    classTeacher = data.get('classTeacher')
    dateEvent = data.get('dateEvent')
    cupo = data.get('cupo')
    startTime = data.get("startTime")
    endTime = data.get("endTime")
    num = 0
    letter = 0
    type = data.get('type')
    nameEvent = data.get('nameEvent')
    cupoNow = 0
    typeData = types_collection.find_one({"name": type})
    typeDescription = typeData["description"]
    typePhoto = typeData["photo"]
    teacherData = users_collection.find_one({"name": classTeacher, "rol": "2"})
    tacherDescription = teacherData["msg"]
    teacherPhoto = teacherData["photo"]
    teacherShort = teacherData["nameShort"]
    events_collection.insert_one({
        'username': "", "teacherShort": teacherShort, "typeDescription": typeDescription, "typePhoto": typePhoto, "tacherDescription": tacherDescription, "teacherPhoto": teacherPhoto,
        "classTeacher": classTeacher, 'date': dateEvent, 'cupo': cupo, 'num': num, 'letter': letter, "startTime": startTime, "endTime": endTime, 'type': type, 'nameEvent': nameEvent,
        'cupoNow': cupoNow, 'members': [], 'WaitList': []
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

    if (user_document and int(user_document.get("main2", 0)) > 0 and user_document.get("dateEndLong") and
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
    # Configurar Flask para que escuche en todas las interfaces de red (0.0.0.0)
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", default=5000)))
