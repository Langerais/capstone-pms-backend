from flask import Blueprint, request, jsonify
from models import db, Guest  # Ensure Guest model is imported from your models.py

guest_management_blueprint = Blueprint('guest_management', __name__)


@guest_management_blueprint.route('/add_guest', methods=['POST'])
def add_guest(): # TODO: TEST TEST TEST TEST TEST TEST !!!
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
        return jsonify(new_guest.to_dict()), 201
    except Exception as e:
        return jsonify(error=str(e)), 500
