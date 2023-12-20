# auth.py
from datetime import timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re

authentication_blueprint = Blueprint('auth', __name__)


@authentication_blueprint.route('/login', methods=['POST'])
def login():  # TESTED : OK;
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = request.json.get('email', '')
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    user = User.query.filter_by(email=email).first()
    print(f"User Department: {user.department}")

    if user and user.check_password(password):
        additional_claims = {"department": user.department}
        access_token = create_access_token(identity=user.email,
                                           additional_claims=additional_claims,
                                           expires_delta=timedelta(days=1))

        #         access_token = create_access_token(identity=user.email,
        #                                            additional_claims=additional_claims,
        #                                            expires_delta=timedelta(days=1))

        print(f"User: {user.email} logged in successfully")
        print(f"Access token: {access_token}")
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad email or password"}), 401


@authentication_blueprint.route('/check_password', methods=['POST'])
def check_password():
    email = request.json.get('email', '')
    password = request.json.get('password', None)

    if not email or not password:
        print("Missing email or password")
        return jsonify({"msg": "Missing email or password"}), 400

    if not is_valid_email(email):
        print("Invalid email format")
        return jsonify({"msg": "Invalid email format"}), 400

    user = User.query.filter_by(email=email).first()
    print(f"User: {user.name}")

    if user and user.check_password(password):
        return jsonify({"msg": "Password is correct"}), 200

    print(user.check_password(password))

    return jsonify({"msg": "Bad email or password"}), 401


@authentication_blueprint.route('/get_user_department', methods=['GET'])
@jwt_required()
def get_user_department():
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if user:
        return jsonify({"department": user.department}), 200

    return jsonify({"msg": "User not found"}), 404


# Decorator to check if user has the required role
def requires_roles(*roles):  # @requires_roles('Admin', 'Manager', 'OtherRole')
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()  # Ensure the user is logged in
            claims = get_jwt()
            if 'department' in claims and claims['department'] in roles:
                return fn(*args, **kwargs)
            return jsonify({"msg": "Access Denied: Insufficient permissions"}), 403

        return wrapper

    return decorator


# Validators:
def is_valid_email(email):  # TESTED OK
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone):  # TESTED OK
    regex = r'^\+?1?\d{9,15}$'
    return re.fullmatch(regex, phone)

# TEST Validators:
# curl -X PUT http://localhost:5000/users/modify_user/1 \
# -H "Content-Type: application/json" \
# -d '{"email": "incorrect-email-format", "phone": "123"}'
