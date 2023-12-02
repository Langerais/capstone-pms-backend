# auth.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash
from models import db, User  # Assuming your User model is defined in models.py
from flask_bcrypt import Bcrypt
import re

auth_blueprint = Blueprint('auth', __name__)
bcrypt = Bcrypt()

@auth_blueprint.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    email = request.json.get('email', '')
    password = request.json.get('password', None)

    if not email or not password:
        return jsonify({"msg": "Missing email or password"}), 400

    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    user = User.query.filter_by(email=email).first()
    #if user and check_password_hash(user.password_hash, password):
    if user and bcrypt.check_password_hash(user.password_hash, password):
        additional_claims = {"department": user.department}
        access_token = create_access_token(identity=user.email, additional_claims=additional_claims)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Bad email or password"}), 401


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None
