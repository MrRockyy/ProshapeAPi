from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from flask_cors import CORS
from bson import json_util, ObjectId
from datetime import datetime, timedelta
import pytz
import os
from bson import ObjectId
from bson.json_util import dumps
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
plans_collection = db['plans']
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
    direction = data.get('direction')
    description = data.get('description')
    descriptionStatus = data.get('descriptionStatus')

    if users_collection.find_one({"username": username}):
        return jsonify({"msg": "Username already exists"}), 400

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "typeDocument": typeDocument, "direction": direction, "description": description, "descriptionStatus": descriptionStatus, "msg": "", "notes": "", "nameShort": "",
        "dateEndShort": "", "dateEndlong": "", "main3": 0, "main2": 0, "main1": 0, "classes": [], "phone": phone, "dateStart": dateStart, "plan": "Sin plan", "rol": "1", "date": date, 
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
@app.route('/api/login/page', methods=['POST'])
def loginPage():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = users_collection.find_one({"username": username, "rol":"3"})

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


################ MEMBERS ###########################

@app.route('/api/clients', methods=['GET'])
@jwt_required()
def get_clients():
    users = users_collection.find({"rol":"1"})
    client_list = []
    for user in users:
            user['_id'] = str(user['_id'])
            client_list.append(user)
    return jsonify(client_list), 200

@app.route('/api/trainers', methods=['GET'])

def get_trainers():
    users = users_collection.find({"rol":"2"})
    client_list = []
    for user in users:
            user['_id'] = str(user['_id'])
            client_list.append(user)
    return jsonify(client_list), 200

@app.route('/api/admins', methods=['GET'])
@jwt_required()
def get_admins():
    users = users_collection.find({"rol":"3"})
    client_list = []
    for user in users:
            user['_id'] = str(user['_id'])
            client_list.append(user)
    return jsonify(client_list), 200

@app.route('/api/user/delete', methods=['POST'])
@jwt_required()
def deleteUSer():
    data = request.get_json()
    current_user = data["_id"]
    result = users_collection.delete_one({"_id": ObjectId(current_user)})
    if result.deleted_count == 1:
        return jsonify({"msg": "User deleted successfully"}), 200
    else:
        return jsonify({"msg": "User not found"}), 404
   
   
@app.route('/api/user/update/password', methods=['PUT'])
@jwt_required()
def updateUserPassword():
    data = request.get_json()
    hashed_password = generate_password_hash(data["password"])
    current_user = data["_id"]
    users_collection.update_one({"_id": ObjectId(current_user)}, {"$set": {"password":hashed_password}})
    return jsonify({"msg": "User updated successfully"}), 200
 



@app.route('/api/user/upgrade', methods=['PUT'])
@jwt_required()
def updateUser():
    data = request.get_json()
    current_user = data["_id"]
    update_fields = {field: data[field] for field in [
        "direction", "description", "descriptionStatus", "msg", "notes", "nameShort",
        "dateEndShort", "dateEndlong", "main3", "main2", "main1", "classes",
        "phone", "dateStart", "plan", "rol", "date", "genre", "photo", "name", "username", "typeDocument"
    ] if field in data}

    if update_fields:
        users_collection.update_one({"_id": ObjectId(current_user)}, {"$set": update_fields})
        return jsonify({"msg": "User updated successfully"}), 200
    else:
        return jsonify({"msg": "No fields to update"}), 400



@app.route('/api/users', methods=['GET'])
def get_users():
    users = users_collection.find({}, {"_id": 0})
    return jsonify([user for user in users]), 200


###############################################
@app.route('/api/types', methods=['POST'])
def types():
    data = request.get_json()
    photo = data.get("photo")
    description = data.get("description")
    name = data.get("name")
    types_collection.insert_one({"photo": photo, "description": description, "name": name})

    return jsonify({"msg": "Type created successfully"}), 201
@app.route('/api/types', methods=['PUT'])
def update_type_by_name():
    data = request.get_json()
    type_id = data.get("_id")
    name = data.get("name")
    photo = data.get("photo")
    description = data.get("description")
    print(type_id)
    

    update_data = {}
    update_data["name"] = name
    if photo is not None:
        update_data["photo"] = photo
    if description is not None:
        update_data["description"] = description

    
    result = types_collection.update_one({"_id": ObjectId(type_id)}, {"$set": update_data})
    if result.matched_count == 0:
            return jsonify({"msg": "Type not found"}), 434
 
    return jsonify({"msg": "Type updated successfully"}), 200


@app.route('/api/types/names', methods=['GET'])
def get_type_names():
    types = types_collection.find({}, {"name": 1, "_id": 0})
    names = [type_['name'] for type_ in types]
    return jsonify({"types": names}), 200

@app.route('/api/types', methods=['GET'])
def get_type():
    types = types_collection.find({})
    # Converting ObjectId to string
    types_list = []
    for type in types:
        type['_id'] = str(type['_id'])
        types_list.append(type)
    return jsonify(types_list), 200

@app.route('/api/types/delete', methods=['POST'])
def delete_type():
    data = request.get_json()
    type_id = data.get('_id')

    if not type_id:
        return jsonify({'message': 'ID is required'}), 400

    try:
        result = types_collection.delete_one({'_id': ObjectId(type_id)})
        if result.deleted_count == 1:
            return jsonify({'message': 'Type deleted successfully'}), 200
        else:
            return jsonify({'message': 'Type not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'message': str(e)}), 400
######################## PLANS ########################################3

@app.route('/api/plans/names', methods=['GET'])
def get_plans_names():
    types = plans_collection.find({}, {"name": 1, "_id": 0})
    names = [type_['name'] for type_ in types]
    return jsonify({"types": names}), 200


@app.route('/api/plans', methods=['GET'])
def get_plans():
    types = plans_collection.find({})
    # Converting ObjectId to string
    types_list = []
    for type in types:
        type['_id'] = str(type['_id'])
        types_list.append(type)
    return jsonify(types_list), 200

@app.route('/api/plans', methods=['POST'])
def plansPost():
    data = request.get_json()
    days = data.get("days")
    description = data.get("description")
    name = data.get("name")
    color = data.get("color")
    plans_collection.insert_one({"days": int(days), "color":color,"description": description, "name": name})

    return jsonify({"msg": "Plan created successfully"}), 201
@app.route('/api/plans', methods=['PUT'])
def update_plans_by_name():
    data = request.get_json()
    type_id = data.get("_id")
    name = data.get("name")
    days = data.get("days")
    color = data.get("color")
    description = data.get("description")
    print(type_id)
    

    update_data = {}
    update_data["color"] =color
    update_data["name"] = name
    if days is not None:
        update_data["days"] = days
    if description is not None:
        update_data["descsiption"] = description

    
    result = plans_collection.update_one({"_id": ObjectId(type_id)}, {"$set": update_data})
    if result.matched_count == 0:
            return jsonify({"msg": "Type not found"}), 434
 
    return jsonify({"msg": "Type updated successfully"}), 200


@app.route('/api/plans/delete', methods=['POST'])
def delete_plan():
    data = request.get_json()
    type_id = data.get('_id')

    if not type_id:
        return jsonify({'message': 'ID is required'}), 400

    try:
        result = plans_collection.delete_one({'_id': ObjectId(type_id)})
        if result.deleted_count == 1:
            return jsonify({'message': 'Type deleted successfully'}), 200
        else:
            return jsonify({'message': 'Type not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'message': str(e)}), 400
#################################################

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
