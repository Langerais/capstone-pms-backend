from flask import Blueprint, request, jsonify
from models import db, Reservation  # Import the Reservation model from models.py

reservations_management_blueprint = Blueprint('reservations_management', __name__)

@reservations_management_blueprint.route('/add_reservation', methods=['POST'])
def add_reservation():
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