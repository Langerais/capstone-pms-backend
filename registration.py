# registration.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Department  # Import your User model
from flask_bcrypt import Bcrypt
from user_management import create_user_logic

registration_blueprint = Blueprint('registration', __name__)
bcrypt = Bcrypt()


@registration_blueprint.route('/register', methods=['POST'])
def register():
    data = request.json
    data['department'] = 'Pending'  # Set department to 'Pending'

    message, status_code = create_user_logic(data)

    if status_code == 201:
        return jsonify({"msg": message}), status_code
    else:
        print(message)
        return jsonify({"error": message}), status_code
