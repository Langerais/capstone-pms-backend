from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

import logs
from auth import requires_roles
from models import db, Guest, User  # Ensure Guest model is imported from your models.py

guest_management_blueprint = Blueprint('guest_management', __name__)


@guest_management_blueprint.route('/add_guest', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception')
def add_guest():
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    data = request.get_json()
    new_guest = Guest(
        name=data['name'],
        surname=data['surname'],
        phone=data['phone'],
        email=data['email']
    )

    # Handle duplicates and other potential errors
    try:
        db.session.add(new_guest)
        db.session.commit()
        log_guest(new_guest, user.id, "Add Guest")
        return jsonify(new_guest.to_dict()), 201
    except Exception as e:
        return jsonify(error=str(e)), 500


@guest_management_blueprint.route('/delete_guest/<int:guest_id>', methods=['DELETE'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception')
def delete_guest(guest_id):
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    guest = Guest.query.get(guest_id)
    if guest:
        try:
            db.session.delete(guest)
            db.session.commit()
            log_guest(guest, user.id, "Delete Guest")
            return jsonify({"msg": "Guest deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Guest not found"}), 404


@guest_management_blueprint.route('/modify_guest/<int:guest_id>', methods=['PUT'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception')
def modify_guest(guest_id):
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    guest = Guest.query.get(guest_id)
    if not guest:
        return jsonify({"msg": "Guest not found"}), 404

    data = request.get_json()
    guest.channel_manager_id = data.get('channel_manager_id', guest.channel_manager_id)
    guest.name = data.get('name', guest.name)
    guest.surname = data.get('surname', guest.surname)
    guest.phone = data.get('phone', guest.phone)
    guest.email = data.get('email', guest.email)

    try:
        db.session.commit()
        log_guest(guest, user.id, "Modify Guest")
        return jsonify({"msg": "Guest updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@guest_management_blueprint.route('/get_guest/<int:guest_id>', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Bar')
def get_guest(guest_id):
    guest = Guest.query.get(guest_id)
    if guest:
        return jsonify(guest.to_dict()), 200
    else:
        return jsonify({"msg": "Guest not found"}), 404


@guest_management_blueprint.route('/get_guests', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Bar')
def get_guests():
    guests = Guest.query.all()
    return jsonify([guest.to_dict() for guest in guests]), 200


@guest_management_blueprint.route('/get_guests_by_ids', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Bar')
def get_guests_by_ids():
    guest_ids = request.json.get('guest_ids', [])
    guests = Guest.query.filter(Guest.id.in_(guest_ids)).all()
    return jsonify([guest.to_dict() for guest in guests]), 200


@guest_management_blueprint.route('/find_guest', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Bar')
def find_guest():
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        phone = data.get('phone', '').lower()

        # Search for a guest with the given email or phone
        guest = Guest.query.filter((Guest.email == email) | (Guest.phone == phone)).first()
        if guest:
            return jsonify(guest.to_dict()), 200
        else:
            return jsonify({"message": "Guest not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def log_guest(guest, user_id, action):
    details = f"ID: {guest.id} |" \
              f"Name: {guest.name} | " \
              f"Surname: {guest.surname} | " \
              f"Phone: {guest.phone} | " \
              f"Email: {guest.email}"

    logs.log_action(user_id, action, details)


