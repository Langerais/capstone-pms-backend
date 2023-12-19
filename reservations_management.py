import logs
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from logs import UserActionLog
from models import db, Reservation, Balance, User, Guest, \
    ReservationStatusChange  # Import the Reservation model from models.py

reservations_management_blueprint = Blueprint('reservations_management', __name__)


@reservations_management_blueprint.route('/add_reservation', methods=['POST'])
# @jwt_required()
# @requires_roles('Admin', 'Manager', 'Reception')
def add_reservation():
    """
    Endpoint to add a new reservation.

    Extracts data from the request and creates a new Reservation entity.
    Commits the new reservation to the database and logs the action.

    :return: JSON response with the newly created reservation.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    new_reservation = Reservation(
        channel_manager_id=data.get('channel_manager_id'),  # TODO: Implement later
        start_date=data.get('start_date'),  # Start date of the reservation
        end_date=data.get('end_date'),  # End date of the reservation
        room_id=data.get('room_id'),  # ID of the reserved room
        guest_id=data.get('guest_id'),  # ID of the guest making the reservation
        due_amount=data.get('due_amount')  # Due amount for the reservation
    )

    try:
        db.session.add(new_reservation)
        db.session.commit()
        log_reservation(new_reservation, user.id, "Reservation Add")
        add_reservation_status_change_internal(new_reservation.id, 'Pending', user.id)
        return jsonify(new_reservation.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@reservations_management_blueprint.route('/delete_reservation/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):  # TODO: TEST
    """
    Endpoint to delete a reservation by ID.

    :param reservation_id: The ID of the reservation to delete.
    :return: JSON response with a success or error message.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    reservation = Reservation.query.get(reservation_id)
    if reservation:
        try:
            db.session.delete(reservation)
            db.session.commit()
            log_reservation(reservation, user.id, "Reservation Delete")
            return jsonify({"msg": "Reservation deleted successfully"}), 200
        except Exception as e:
            print(e)
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Reservation not found"}), 404


# TEST delete_reservation
# curl -X DELETE http://localhost:5000/reservations/delete_reservation/1


@reservations_management_blueprint.route('/modify_reservation/<int:reservation_id>', methods=['PUT'])
def modify_reservation(reservation_id):  # TODO: TEST
    """
    Endpoint to modify a reservation by ID.

    If request has data for a field, update that field in the reservation.
    If request has no data for a field, keep the field's current value.

    :param reservation_id: The ID of the reservation to modify.
    :return: JSON response with a success or error message.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)
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
        log_reservation(reservation, user.id, "Reservation Modify")
        return jsonify({"msg": "Reservation updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# TEST modify_reservation
# curl -X PUT http://localhost:5000/reservations/modify_reservation/1 \
# -H "Content-Type: application/json" \
# -d '{"channel_manager_id": "newID", "due_amount": 300.00}'

@reservations_management_blueprint.route('/change_reservation_status/<int:reservation_id>', methods=['PUT'])
def change_reservation_status(reservation_id):
    """
    Endpoint to change the status of a reservation by ID.

    :param reservation_id: The ID of the reservation to modify.
    :return: JSON response with a success or error message.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)
    reservation = Reservation.query.get(reservation_id)
    if not reservation:
        return jsonify({"msg": "Reservation not found"}), 404

    data = request.get_json()
    new_status = data.get('status')

    print(new_status)

    # You may want to validate the new status here if necessary
    if new_status not in ['Pending', 'Checked-in', 'Checked-out']:
        return jsonify({"error": "Invalid status"}), 400

    reservation.status = new_status

    try:
        db.session.commit()
        log_reservation(reservation, user.id, "Reservation Status-Change")
        add_reservation_status_change_internal(reservation_id, new_status, user.id)
        return jsonify({"msg": "Reservation status updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


def add_reservation_status_change_internal(reservation_id, new_status, user_id):
    """
    Function to add a reservation status change internally.

    :param reservation_id: ID of the reservation.
    :param new_status: New status of the reservation.
    :return: None or raises an exception if an error occurs.
    """
    if new_status not in ['Checked-in', 'Checked-out', 'Pending']:
        raise ValueError("Invalid status provided")

    reservation_status_change = ReservationStatusChange(
        reservation_id=reservation_id,
        status=new_status,
        user_id=user_id
    )

    try:
        db.session.add(reservation_status_change)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


@reservations_management_blueprint.route('/get_reservation_status_changes', methods=['GET'])
def get_all_reservation_status_changes():
    changes = ReservationStatusChange.query.all()
    return jsonify([change.to_dict() for change in changes]), 200


@reservations_management_blueprint.route('/get_reservation_status_changes/<int:reservation_id>', methods=['GET'])
def get_reservation_status_change_by_reservation(reservation_id):
    change = ReservationStatusChange.query.filter_by(reservation_id=reservation_id).all()
    if change:
        return jsonify([c.to_dict() for c in change]), 200
    else:
        return jsonify({"error": "Status change not found"}), 404



@reservations_management_blueprint.route('/get_reservation/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):  # Tested

    """
    Endpoint to get a reservation by ID.

    :param reservation_id: The ID of the reservation to get.
    :return: JSON response with reservation and success or error message.
    """
    reservation = Reservation.query.get(reservation_id)
    if reservation:
        return jsonify(reservation.to_dict()), 200
    else:
        return jsonify({"msg": "Reservation not found"}), 404


# TEST get_reservation
# curl -X GET http://localhost:5000/reservations/get_reservation/1

@reservations_management_blueprint.route('/get_reservations', methods=['GET'])
def get_reservations():  # TESTED
    """
    Endpoint to get all reservations.

    :return: JSON response with a list of all reservations and a success or error message.
    """
    reservations = Reservation.query.all()
    return jsonify([reservation.to_dict() for reservation in reservations]), 200


@reservations_management_blueprint.route('/get_guest_reservations/<int:guest_id>', methods=['GET'])
def get_guest_reservations(guest_id):  # TESTED: OK

    """
    Endpoint to get all reservations for a given guest.

    :param guest_id: The ID of the guest to get reservations for.
    :return: JSON response with a list of all reservations for the guest and a success or error message.
    """
    reservations = Reservation.query.filter_by(guest_id=guest_id)
    return jsonify([reservation.to_dict() for reservation in reservations]), 200


# get reservations intersecting with a given date range
@reservations_management_blueprint.route('/get_reservations_by_date_range', methods=['GET'])
def get_reservations_by_date_range():  # TESTED: OK

    """
    Endpoint to get all reservations intersecting with a given date range.

    :return: JSON response with a list of all reservations intersecting with a given date range and a success or error message.
    """

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    reservations = Reservation.query.filter(Reservation.start_date <= end_date, Reservation.end_date >= start_date)
    return jsonify([reservation.to_dict() for reservation in reservations]), 200


@reservations_management_blueprint.route('/get_reservations_by_room_and_date_range', methods=['GET'])
def get_reservations_by_room_and_date_range():
    """
    Endpoint to get all reservations for a given room intersecting with a given date range.

    :return: JSON response with a list of all reservations for a given room intersecting with a given date range and a success or error message.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    room_id = request.args.get('room_id')

    try:
        room_id = int(room_id)  # Convert room_id to integer
    except ValueError:
        return jsonify({"error": "Invalid room_id"}), 400

    reservations = Reservation.query.filter(
        Reservation.start_date <= end_date,
        Reservation.end_date >= start_date,
        Reservation.room_id == room_id
    ).all()

    return jsonify([reservation.to_dict() for reservation in reservations]), 200


# Calculate the unpaid amount for a given reservation (Restaurant only)
@reservations_management_blueprint.route('/calculate_unpaid_amount/<int:reservation_id>', methods=['GET'])
def calculate_unpaid_amount(reservation_id):
    """
    Endpoint to calculate the unpaid amount for a given reservation (Restaurant only)
    :param reservation_id: The ID of the reservation to calculate the unpaid amount for.
    :return: JSON response with the unpaid amount and a success or error message.
    """
    balance_entries = Balance.query.filter_by(reservation_id=reservation_id).all()

    total_charges = sum(entry.amount for entry in balance_entries if entry.menu_item_id > 0)
    total_payments = sum(entry.amount for entry in balance_entries if entry.menu_item_id in [0, -1])

    unpaid_amount = total_charges + total_payments  # Payments are negative amounts
    return jsonify({'unpaid_amount': str(unpaid_amount)}), 200


def calculate_unpaid_amount_internal(reservation_id):
    """
    Endpoint to calculate the unpaid amount for a given reservation (Restaurant only)
    :param reservation_id: The ID of the reservation to calculate the unpaid amount for.
    :return: JSON response with the unpaid amount and a success or error message.
    """
    balance_entries = Balance.query.filter_by(reservation_id=reservation_id).all()

    total_charges = sum(entry.amount for entry in balance_entries if entry.menu_item_id > 0)
    total_payments = sum(entry.amount for entry in balance_entries if entry.menu_item_id in [0, -1])

    unpaid_amount = total_charges + total_payments  # Payments are negative amounts
    return unpaid_amount


def log_reservation(reservation, user_id, action):

    """
    Helper function to log a reservation action.
    :param reservation: The reservation to log.
    :param user_id: The ID of the user performing the action.
    :param action: The action to log.
    :return: None
    """
    guest = Guest.query.get(reservation.guest_id)
    details = f"Reservation Id: {reservation.id}" \
              f" | Room: {reservation.room_id}" \
              f" | Guest: {guest.name} {guest.surname}" \
              f" | From: {reservation.start_date}" \
              f" | To: {reservation.end_date}" \
              f" | Status: {reservation.status}" \
              f" | Due Amount: {reservation.due_amount}"
    logs.log_action(user_id, action, details)
