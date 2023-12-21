# user_management.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError
import auth
import logs
from models import db, User, Department  # Import the necessary models

user_management_blueprint = Blueprint('users', __name__)


@user_management_blueprint.route('/create_user', methods=['POST'])
@jwt_required()
@auth.requires_roles('Admin', 'Manager')
def create_user():  # TESTED
    """
    Create a new user.
    Returns:
        JSON response with a success message or error message and status code.

    """
    data = request.get_json()
    message, status_code = create_user_logic(data)
    return jsonify(message), status_code


def create_user_logic(data):
    """
    Logic for creating a new user.

    Args:
        data (dict): User data including name, surname, phone, email, department, and password.

    Returns:
        Tuple containing a JSON response message and status code.

    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user_who_created = User.query.filter_by(email=current_user_email).first()

    name = data.get('name')
    surname = data.get('surname')
    phone = data.get('phone')  # Validate phone number
    email = data.get('email')  # Validate email
    department = data.get('department')
    password = data.get('password')

    if not all([name, surname, phone, email, password, department]):
        return "Missing required fields", 400

    if not auth.is_valid_email(email):
        return "Invalid email format", 400

    if not auth.is_valid_phone(phone):
        return "Invalid phone number format", 400

    # Check if department exists
    if not Department.query.filter_by(department_name=department).first():
        return "Invalid department", 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User with this email already exists"}), 409

    new_user = User(name=name, surname=surname, phone=phone, email=email, department=department)
    new_user.set_password(password)  # Use the set_password method from the User model

    try:
        db.session.add(new_user)
        db.session.commit()
        log_user(new_user, user_who_created.id, "Create User")
        return "User created successfully", 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return f"Database error: {str(e)}", 500


@user_management_blueprint.route('/modify_user/<int:user_id>', methods=['PUT'])
@jwt_required()
@auth.requires_roles('Admin', 'Manager', 'Cleaning', 'Reception', 'Bar', 'Pending')
def modify_user(user_id):  # Tested
    """
    Modify an existing user's details.

    Args:
        user_id (int): The ID of the user to be modified.

    Returns:
        JSON response with a success message or error message and status code.

    Explanation:
        - Retrieves JSON data from the request, including fields like 'name', 'surname', 'phone',
          'email', and 'department'. If these fields are not provided in the JSON data, the
          existing user data will be used for those fields.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user_who_changed = User.query.filter_by(email=current_user_email).first()

    user = User.query.get(user_id)

    # Check if the user attempting to modify the user is the same user or an admin/manager
    if user_who_changed.id != user_id and not auth.requires_roles('Admin', 'Manager'):
        return jsonify({"msg": "You do not have permission to modify this user"}), 403

    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    name = data.get('name', user.name)
    surname = data.get('surname', user.surname)
    phone = data.get('phone', user.phone)
    email = data.get('email', user.email)
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
        log_user(user, user_who_changed.id, "Modify User")
        return jsonify({"msg": "User updated successfully"}), 200
    except Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# TEST modify_user:
# curl -X PUT http://localhost:5000/users/modify_user/1 \
# -H "Content-Type: application/json" \
# -d '{"name": "NewJohn", "surname": "NewDoe", "phone": "123456789", "email": "john.doe@gmail.com", "department": "Manager"}'


@user_management_blueprint.route('/change_password/<int:user_id>', methods=['PUT'])
@jwt_required()
@auth.requires_roles('Admin', 'Manager', 'Reception', 'Cleaning', 'Bar')
def change_password():
    """
    Change a user's password (By user itself).

    Returns:
        JSON response with a success message or error message and status code.


    Explanation:
        - Retrieves JSON data from the request, including 'old_password' and 'new_password'.
          Both fields are required. It checks if the 'old_password' matches the user's
          current password and then updates the password with 'new_password'.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        print("Missing required fields")
        return jsonify({"msg": "Missing required fields"}), 400

    if not user.check_password(old_password):
        print("Invalid password")
        return jsonify({"msg": "Invalid password"}), 400

    user.set_password(new_password)

    try:
        db.session.commit()
        log_user(user, user.id, "Change UserPassword")
        return jsonify({"msg": "Password updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_management_blueprint.route('/change_password_manager/<int:user_id>', methods=['PUT'])
@jwt_required()
@auth.requires_roles('Admin', 'Manager')
def change_password_manager(user_id):  # Tested
    """
    Change a user's password (by manager or admin).

    Args:
        user_id (int): The ID of the user whose password will be changed.

    Returns:
        JSON response with a success message or error message and status code.

    Explanation:
        - Retrieves JSON data from the request, including 'manager_password' and 'new_password'.
          Both fields are required. It checks if the 'manager_password' matches the manager's
          current password and then updates the user's password with 'new_password'.
    """

    current_user_email = get_jwt_identity()  # Get the user's email from the token
    manager = User.query.filter_by(email=current_user_email).first()

    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not manager:
        return jsonify({"msg": "Manager not found"}), 404

    data = request.get_json()
    manager_password = data.get('manager_password')
    new_password = data.get('new_password')

    is_password_correct = manager.check_password(manager_password)
    print(f"Is Manager Password Correct: {is_password_correct}")

    if not is_password_correct:
        return jsonify({"msg": "Invalid manager password"}), 400

    if not manager_password or not new_password:
        print("Missing required fields")
        return jsonify({"msg": "Missing required fields"}), 400

    if not manager.check_password(manager_password):
        print("Invalid password")
        return jsonify({"msg": "Invalid manager password"}), 400

    user.set_password(new_password)

    try:
        db.session.commit()
        log_user(user, user_id, "Change UserPassword by Manager")
        return jsonify({"msg": "Password updated successfully"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@user_management_blueprint.route('/change_department/<int:user_id>', methods=['PUT'])
@jwt_required()
@auth.requires_roles('Admin', 'Manager')
def change_department(user_id):  # TESTED: OK
    """
    Change a user's department.

    Args:
        user_id (int): The ID of the user whose department will be changed.

    Returns:
        JSON response with a success message or error message and status code.

    Explanation:
        - Retrieves JSON data from the request, including 'department'.
          It checks if the 'department' exists in the database and then updates
          the user's department.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    manager = User.query.filter_by(email=current_user_email).first()

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
        log_user(user, manager.id, "Change UserDepartment")
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
@jwt_required()
def get_user(user_id):
    """
    Get a user's details by ID.

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        JSON response with user details or error message and status code.
    """
    user = get_user_logic(user_id)
    print(user.name)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user.to_dict()), 200


def get_user_logic(user_id):
    user = User.query.get(user_id)
    print(user.name)
    return user


# Endpoint to get user by email
@user_management_blueprint.route('/get_user_by_email/<string:email>', methods=['GET'])
@jwt_required()
def get_user_by_email(email):
    """
    Get a user's details by email.

    Args:
        email (str): The email of the user to retrieve.

    Returns:
        JSON response with user details or error message and status code.
    """
    user = get_user_by_email_logic(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user.to_dict()), 200


def get_user_by_email_logic(email):
    user = User.query.filter_by(email=email).first()
    return user


# Function to get all users using separate function get_users_logic
@user_management_blueprint.route('/get_users', methods=['GET'])
@jwt_required()
def get_users():
    """
    Get a list of all departments.

    Returns:
        JSON response with a list of departments and status code.
    """
    users = get_users_logic()
    return jsonify([user.to_dict() for user in users]), 200


def get_users_logic():
    users = User.query.all()
    return users


# Function to get all users by department using separate function get_users_by_department_logic
@user_management_blueprint.route('/get_all_users_by_department/<string:department>', methods=['GET'])
@jwt_required()
def get_users_by_department(department):
    """
    Get a list of all users in a specific department.

    Args:
        department (str): The department name to filter by.

    Returns:
        JSON response with a list of user details or error message and status code.
    """
    users = get_users_by_department_logic(department)
    return jsonify([user.to_dict() for user in users]), 200


def get_users_by_department_logic(department):
    users = User.query.filter_by(department=department).all()
    return users


@user_management_blueprint.route('/get_all_departments', methods=['GET'])
@jwt_required()
def get_all_departments():
    """
    Get a list of all available departments.

    Returns:
        JSON response with a list of department details or error message and status code.
    """
    departments = Department.query.all()
    return jsonify([department.to_dict() for department in departments]), 200


# Function to log actions performed with user entities using logs.py similar to:


def log_user(user, user_id, action):
    """
    Log user-related actions and details.

    Args:
        user (User): The user entity for which the action is being logged.
        user_id (int): The ID of the user involved in the action.
        action (str): The action being performed, such as "Create User" or "Modify User".

    Logs the details of the action along with user information.

    Example of logged details:
    "ID: 4 | Name: John | Surname: Doe | Phone: 123456789 | Email: john@example.com | Department: IT"

    The logged information can be used for auditing and tracking user-related activities.

    Returns:
        None
    """
    details = f"ID: {user.id} |" \
              f"Name: {user.name} | " \
              f"Surname: {user.surname} | " \
              f"Phone: {user.phone} | " \
              f"Email: {user.email} | " \
              f"Department: {user.department}"

    logs.log_action(user_id, action, details)
