from flask import Blueprint, jsonify
from models import Room

get_entities_blueprint = Blueprint('get_entities_blueprint', __name__)

@get_entities_blueprint.route('/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms])
