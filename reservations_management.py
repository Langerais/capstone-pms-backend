from flask import Blueprint, request, jsonify
from models import db, Reservation  # Import the Reservation model from models.py

reservations_management_blueprint = Blueprint('reservations_management', __name__)

@reservations_management_blueprint.route('/add_reservation', methods=['POST'])
def add_reservation(): # TODO: TEST TEST TEST TEST TEST TEST !!!
    data = request.get_json()
    new_reservation = Reservation(
        channel_manager_id=data.get('channel_manager_id'),
        start_date=data.get('start_date'),
        end_date=data.get('end_date'),
        room_id=data.get('room_id'),
        guest_id=data.get('guest_id'),
        due_amount=data.get('due_amount')
    )

    try:
        db.session.add(new_reservation)
        db.session.commit()
        return jsonify(new_reservation.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@reservations_management_blueprint.route('/delete_reservation/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if reservation:
        try:
            db.session.delete(reservation)
            db.session.commit()
            return jsonify({"msg": "Reservation deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Reservation not found"}), 404

# TEST delete_reservation
# curl -X DELETE http://localhost:5000/reservations/delete_reservation/1


@reservations_management_blueprint.route('/modify_reservation/<int:reservation_id>', methods=['PUT'])
def modify_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    data = request.get_json()
    reservation.channel_manager_id = data.get('channel_manager_id', reservation.channel_manager_id)
    reservation.start_date = data.get('start_date', reservation.start_date)
    reservation.end_date = data.get('end_date', reservation.end_date)
    reservation.room_id = data.get('room_id', reservation.room_id)
    reservation.guest_id = data.get('guest_id', reservation.guest_id)
    reservation.due_amount = data.get('due_amount', reservation.due_amount)

    try:
        db.session.commit()
        return jsonify({"msg": "Reservation updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# TEST modify_reservation
# curl -X PUT http://localhost:5000/reservations/modify_reservation/1 \
# -H "Content-Type: application/json" \
# -d '{"channel_manager_id": "newID", "due_amount": 300.00}'

@reservations_management_blueprint.route('/get_reservation/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if reservation:
        return jsonify(reservation.to_dict()), 200
    else:
        return jsonify({"msg": "Reservation not found"}), 404

# TEST get_reservation
# curl -X GET http://localhost:5000/reservations/get_reservation/1

@reservations_management_blueprint.route('/get_reservations', methods=['GET'])
def get_reservations():  # TODO: TEST TEST TEST TEST TEST TEST !!!
    reservations = Reservation.query.all()
    return jsonify([reservation.to_dict() for reservation in reservations]), 200

# TODO: get_guest_reservations(guest_id)

@reservations_management_blueprint.route('/get_guest_reservations/<int:guest_id>', methods=['GET'])
def get_guest_reservations(guest_id):
    reservations = Reservation.query.filter_by(guest_id=guest_id)
    return jsonify([reservation.to_dict() for reservation in reservations]), 200
