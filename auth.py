# auth.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from models import db, User
from flask_bcrypt import Bcrypt
from functools import wraps
import re

auth_blueprint = Blueprint('auth', __name__)
bcrypt = Bcrypt()


@auth_blueprint.route('/login', methods=['POST'])
def login():  # TODO: Logout!!!
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = request.json.get('email', '')
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password_hash, password):
        additional_claims = {"department": user.department}
        access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad email or password"}), 401


@auth_blueprint.route('/get_user_department', methods=['GET'])
@jwt_required()
def get_user_department():  # TODO: TEST TEST TEST TEST TEST TEST !!!
    user_email = get_jwt_identity()
    user = User.query.filter_by(email=user_email).first()

    if user:
        return jsonify({"department": user.department}), 200

    return jsonify({"msg": "User not found"}), 404


# Decorator to check if user has the required role
def requires_role(role):  # TODO: Add access control to all functions that require it (@requires_role('Admin'))
    def decorator(fn):  # TODO: TEST TEST TEST TEST TEST TEST !!!
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()  # Ensure the user is logged in
            claims = get_jwt()
            if 'department' in claims and claims['department'] == role:
                return fn(*args, **kwargs)
            return jsonify({"msg": "Access Denied : Insufficient permissions"}), 403

        return wrapper

    return decorator


# Validators:
def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    # Modify this regex according to your needs for phone number validation
    regex = r'^\+?1?\d{9,15}$'
    return re.fullmatch(regex, phone)

# TEST Validators:
# curl -X PUT http://localhost:5000/users/modify_user/1 \
# -H "Content-Type: application/json" \
# -d '{"email": "incorrect-email-format", "phone": "123"}'
