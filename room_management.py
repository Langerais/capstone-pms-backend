# room_management.py

from flask import Blueprint, request, jsonify
from models import db, Room, RoomCleaningStatus  # Import the necessary models

room_management_blueprint = Blueprint('room_management', __name__)


@room_management_blueprint.route('/create_room', methods=['POST'])
def create_room(): # TODO: TEST
    data = request.get_json()
    channel_manager_id = data.get('channel_manager_id')
    room_name = data.get('room_name')
    max_guests = data.get('max_guests')
    number_of_beds = data.get('number_of_beds')

    if not room_name or max_guests is None or number_of_beds is None:
        return jsonify({"msg": "Missing required room data"}), 400

    new_room = Room(
        channel_manager_id=channel_manager_id,
        room_name=room_name,
        max_guests=max_guests,
        number_of_beds=number_of_beds
    )

    try:
        db.session.add(new_room)
        db.session.commit()

        # Initialize the cleaning status for the new room
        initial_status = RoomCleaningStatus(room_id=new_room.id, status='cleaned')
        db.session.add(initial_status)
        db.session.commit()

        return jsonify(new_room.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@room_management_blueprint.route('/get_rooms', methods=['GET'])
def get_rooms():  # TESTED: OK
    rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms]), 200


@room_management_blueprint.route('/get_room/<int:room_id>', methods=['GET'])
def get_room(room_id): # TODO: TEST
    room = Room.query.get(room_id)
    if room:
        return jsonify(room.to_dict()), 200
    return jsonify({"msg": "Room not found"}), 404


@room_management_blueprint.route('/remove_room/<int:room_id>', methods=['DELETE'])
def remove_room(room_id): # TODO: TEST
    room = Room.query.get(room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        return jsonify({"msg": "Room removed"}), 200
    return jsonify({"msg": "Room not found"}), 404


@room_management_blueprint.route('/edit_room/<int:room_id>', methods=['PUT'])
def edit_room(room_id): # TODO: TEST
    room = Room.query.get(room_id)
    if room:
        data = request.get_json()
        room.channel_manager_id = data.get('channel_manager_id', room.channel_manager_id)
        room.room_name = data.get('room_name', room.room_name)
        room.max_guests = data.get('max_guests', room.max_guests)
        room.number_of_beds = data.get('number_of_beds', room.number_of_beds)

        db.session.commit()
        return jsonify(room.to_dict()), 200
    return jsonify({"msg": "Room not found"}), 404


@room_management_blueprint.route('/update_room_status/<int:room_id>', methods=['PUT'])
def update_room_status(room_id): # TODO: TEST
    data = request.get_json()
    status = data.get('status')

    # Validate status
    if status not in ['requires-cleaning', 'cleaning', 'cleaned']:
        return jsonify({"msg": "Invalid status"}), 400

    new_status = RoomCleaningStatus(room_id=room_id, status=status)

    try:
        db.session.add(new_status)
        db.session.commit()
        return jsonify({"msg": "Room status updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@room_management_blueprint.route('/get_room_status/<int:room_id>', methods=['GET'])
def get_room_status(room_id): # TODO: TEST
    latest_status = RoomCleaningStatus.query \
        .filter_by(room_id=room_id) \
        .order_by(RoomCleaningStatus.updated_at.desc()) \
        .first()

    if latest_status:
        return jsonify({
            'room_id': room_id,
            'status': latest_status.status,
            'updated_at': latest_status.updated_at
        }), 200

    return jsonify({"msg": "Room status not found"}), 404
