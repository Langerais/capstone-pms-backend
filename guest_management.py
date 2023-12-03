from flask import Blueprint, request, jsonify
from models import db, Guest  # Ensure Guest model is imported from your models.py

guest_management_blueprint = Blueprint('guest_management', __name__)


@guest_management_blueprint.route('/add_guest', methods=['POST'])
def add_guest(): # TODO: TEST TEST TEST TEST TEST TEST !!!
    data = request.get_json()
    new_guest = Guest(
        channel_manager_id=data['channel_manager_id'],
        name=data['name'],
        surname=data['surname'],
        phone=data['phone'],
        email=data['email']
    )

    # Handle duplicates and other potential errors
    try:
        db.session.add(new_guest)
        db.session.commit()
        return jsonify(new_guest.to_dict()), 201
    except Exception as e:
        return jsonify(error=str(e)), 500


@guest_management_blueprint.route('/delete_guest/<int:guest_id>', methods=['DELETE'])
def delete_guest(guest_id):
    guest = Guest.query.get(guest_id)
    if guest:
        try:
            db.session.delete(guest)
            db.session.commit()
            return jsonify({"msg": "Guest deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Guest not found"}), 404


@guest_management_blueprint.route('/modify_guest/<int:guest_id>', methods=['PUT'])
def modify_guest(guest_id):
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
        return jsonify({"msg": "Guest updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@guest_management_blueprint.route('/get_guest/<int:guest_id>', methods=['GET'])
def get_guest(guest_id):
    guest = Guest.query.get(guest_id)
    if guest:
        return jsonify(guest.to_dict()), 200
    else:
        return jsonify({"msg": "Guest not found"}), 404


@guest_management_blueprint.route('/get_guests', methods=['GET'])
def get_guests():  # TODO: TEST TEST TEST TEST TEST TEST !!!
    guests = Guest.query.all()
    return jsonify([guest.to_dict() for guest in guests]), 200
