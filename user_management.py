# user_management.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
import auth
import logs
from models import db, User, Department  # Import the necessary models

user_management_blueprint = Blueprint('users', __name__)


@user_management_blueprint.route('/create_user', methods=['POST'])
def create_user():  # TODO: TEST
    data = request.get_json()
    message, status_code = create_user_logic(data)
    return jsonify(message), status_code


def create_user_logic(data):
    name = data.get('name')
    surname = data.get('surname')
    phone = data.get('phone')  # Validate phone number
    email = data.get('email')  # Validate email
    department = data.get('department')
    password = data.get('password')

    if not all([name, surname, phone, email, password, department]):
        return jsonify({"msg": "Missing required fields"}), 400

    if not auth.is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    if not auth.is_valid_phone(phone):
        return jsonify({"msg": "Invalid phone number format"}), 400

    # Check if department exists
    if not Department.query.filter_by(department_name=department).first():
        return jsonify({"msg": "Invalid department"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User with this email already exists"}), 409

    new_user = User(name=name, surname=surname, phone=phone, email=email, department=department)
    new_user.set_password(password)  # Use the set_password method from the User model

    try:
        db.session.add(new_user)
        db.session.commit()
        log_user(new_user, new_user.id, "Create User")
        return jsonify({"msg": "User created successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_management_blueprint.route('/modify_user/<int:user_id>', methods=['PUT'])
def modify_user(user_id):  # TODO: TEST
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    name = data.get('name', user.name)
    surname = data.get('surname', user.surname)
    phone = data.get('phone', user.phone)  # TODO: Validate phone number
    email = data.get('email', user.email)  # TODO: Validate email
    department = data.get('department', user.department)

    if email and not auth.is_valid_email(email):
        return jsonify({"msg": "Invalid email format"}), 400

    if phone and not auth.is_valid_phone(phone):
        return jsonify({"msg": "Invalid phone number format"}), 400

    # Validate if the department exists
    if department and not Department.query.filter_by(department_name=department).first():
        return jsonify({"msg": "Invalid department"}), 400

    user.name = name
    user.surname = surname
    user.phone = phone
    user.email = email
    user.department = department

    try:
        db.session.commit()
        log_user(user, user_id, "Modify User")
        return jsonify({"msg": "User updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# TEST modify_user:
# curl -X PUT http://localhost:5000/users/modify_user/1 \
# -H "Content-Type: application/json" \
# -d '{"name": "NewJohn", "surname": "NewDoe", "phone": "123456789", "email": "john.doe@gmail.com", "department": "Manager"}'


@user_management_blueprint.route('/change_department/<int:user_id>', methods=['PUT'])
def change_department(user_id):  # TESTED: OK
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    new_department = data.get('department')

    # Check if the new department exists
    if not Department.query.filter_by(department_name=new_department).first():
        return jsonify({"msg": "Invalid department"}), 400

    user.department = new_department

    try:
        db.session.commit()
        log_user(user, user_id, "Change UserDepartment")
        return jsonify({"msg": "Department updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# TEST change_department:
# curl -X PUT http://localhost:5000/users/change_department/1 \
# -H "Content-Type: application/json" \
# -d '{"department": "Manager"}'


# Function to get user by id using separate function get_user_logic
@user_management_blueprint.route('/get_user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_logic(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user.to_dict()), 200


def get_user_logic(user_id):
    user = User.query.get(user_id)
    return user


# Function to get all users using separate function get_users_logic
@user_management_blueprint.route('/get_users', methods=['GET'])
def get_users():
    users = get_users_logic()
    return jsonify([user.to_dict() for user in users]), 200


def get_users_logic():
    users = User.query.all()
    return users


# Function to get all users by department using separate function get_users_by_department_logic
@user_management_blueprint.route('/get_all_users_by_department/<string:department>', methods=['GET'])
def get_users_by_department(department):
    users = get_users_by_department_logic(department)
    return jsonify([user.to_dict() for user in users]), 200


def get_users_by_department_logic(department):
    users = User.query.filter_by(department=department).all()
    return users



# Function to log actions performed with user entities using logs.py similar to:


def log_user(user, user_id, action):
    details = f"ID: {user.id} |" \
              f"Name: {user.name} | " \
              f"Surname: {user.surname} | " \
              f"Phone: {user.phone} | " \
              f"Email: {user.email} | " \
              f"Department: {user.department}"

    logs.log_action(user_id, action, details)
