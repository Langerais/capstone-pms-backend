# registration.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import db, User  # Import your User model
from flask_bcrypt import Bcrypt

registration_blueprint = Blueprint('registration', __name__)
bcrypt = Bcrypt()


@registration_blueprint.route('/register', methods=['POST'])
def register():
    data = request.json

    name = data.get('name')
    surname = data.get('surname')
    phone = data.get('phone')
    email = data.get('email')
    department = data.get('department')
    password = data.get('password')

    if not name or not surname or not phone or not email or not password or not department:
        return jsonify({"msg": "Missing required fields"}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"msg": "User with this email already exists"}), 409

    new_user = User(name=name, surname=surname, phone=phone, email=email, department=department)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "User registered successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction on error
        return jsonify({"error": str(e)}), 500
