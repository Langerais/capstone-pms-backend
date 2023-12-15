"""
This module defines routes for menu management in a restaurant application.
It includes routes for creating, modifying, deleting, and retrieving menu categories and items,
as well as managing balance entries related to menu transactions.

Routes are protected with JWT authentication and role-based access control,
allowing only authorized personnel (like Admin and Manager) to make changes to the menu and balance entries.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required  # Will be used later

import logs
from auth import requires_roles  # Will be used later
from models import db, MenuCategory, MenuItem, Balance, Reservation, Room, User, Guest

menu_management_blueprint = Blueprint('menu_management', __name__)


@menu_management_blueprint.route('/create_category', methods=['POST'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def create_category():
    """
    Creates a new menu category.

    This endpoint handles POST requests to create a new category for the menu.
    It requires the category name in the request JSON.

    Returns:
        - JSON response with the newly created category and status code 201 on success.
        - JSON response with error message and status code 400 if category name is missing.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"msg": "Missing category name"}), 400

    new_category = MenuCategory(name=name)
    # Attempt to add new category to the database
    try:
        db.session.add(new_category)
        db.session.commit()
        log_category(new_category, user.id, "Add MenuCategory")
        return jsonify(new_category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Similar comments should be added for each of the remaining routes
# I'll provide an example for one more route for brevity

@menu_management_blueprint.route('/remove_category/<int:category_id>', methods=['DELETE'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def remove_category(category_id):
    """
    Deletes a menu category.

    This endpoint handles DELETE requests to remove a specific category by its ID.

    Parameters:
        - category_id (int): The ID of the category to be removed.

    Returns:
        - JSON response with success message and status code 200 on successful deletion.
        - JSON response with error message and status code 404 if category is not found.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    category = MenuCategory.query.get(category_id)
    if category:
        try:
            db.session.delete(category)
            db.session.commit()
            log_category(category, user.id, "Delete MenuCategory")
            return jsonify({"msg": "Category removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Category not found"}), 404


@menu_management_blueprint.route('/modify_category/<int:category_id>', methods=['PUT'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def modify_category(category_id):
    """
    Modifies an existing menu category.

    This endpoint handles PUT requests to update the name of a specific menu category
    identified by 'category_id'. It expects an updated name in the request JSON.

    Parameters:
        - category_id (int): The ID of the category to be modified.

    Returns:
        - JSON response with the updated category data and status code 200 on success.
        - JSON response with error message and status code 404 if the category is not found.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    category = MenuCategory.query.get(category_id)
    if category:
        data = request.get_json()
        name = data.get('name')
        if name is not None:
            category.name = name

        try:
            db.session.commit()
            log_category(category, user.id, "Modify MenuCategory")
            return jsonify(category.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Category not found"}), 404


@menu_management_blueprint.route('/get_categories', methods=['GET'])
def get_categories():
    """
    Retrieves all menu categories.

    This endpoint handles GET requests to fetch all existing menu categories.

    Returns:
        - JSON response with a list of menu categories and status code 200 on success.
        - JSON response with error message and status code 500 on server error.
    """
    categories = MenuCategory.query.filter(MenuCategory.id != -1, MenuCategory.id != 0).all()
    return jsonify([category.to_dict() for category in categories]), 200


# Menu item management routes
@menu_management_blueprint.route('/create_item', methods=['POST'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def create_item():
    """
    Creates a new menu item.

    This endpoint handles POST requests to add a new item to the menu.
    It requires item name, category ID, description, and price in the request JSON.

    Returns:
        - JSON response with the newly created item and status code 201 on success.
        - JSON response with error message and status code 400 if required data is missing.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    data = request.get_json()
    name = data.get('name')
    category_id = data.get('category_id')
    description = data.get('description')
    price = data.get('price')

    if not name or not category_id or price is None:
        return jsonify({"msg": "Missing required item data"}), 400

    new_item = MenuItem(name=name, category_id=category_id, description=description, price=price)

    try:
        db.session.add(new_item)
        db.session.commit()

        log_item(new_item, user.id, 'Add MenuItem')

        return jsonify(new_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@menu_management_blueprint.route('/remove_item/<int:item_id>', methods=['DELETE'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def remove_item(item_id):
    """
    Deletes a menu item.

    This endpoint handles DELETE requests to remove a specific menu item by its ID.

    Parameters:
        - item_id (int): The ID of the item to be removed.

    Returns:
        - JSON response with success message and status code 200 on successful deletion.
        - JSON response with error message and status code 404 if item is not found.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    item = MenuItem.query.get(item_id)
    if item:
        try:
            db.session.delete(item)
            db.session.commit()
            log_item(item, user.id, 'Delete MenuItem')
            return jsonify({"msg": "Item removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Item not found"}), 404


@menu_management_blueprint.route('/modify_item/<int:item_id>', methods=['PUT'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def modify_item(item_id):
    """
    Modifies an existing menu item.

    This endpoint handles PUT requests to update the details of a menu item
    identified by 'item_id'. It expects updated item name, category ID, description,
    and price in the request JSON.

    Parameters:
        - item_id (int): The ID of the item to be modified.

    Returns:
        - JSON response with the updated item data and status code 200 on success.
        - JSON response with error message and status code 404 if the item is not found.
        - JSON response with error message and status code 500 on server error.
    """

    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    item = MenuItem.query.get(item_id)
    if item:
        data = request.get_json()
        name = data.get('name')
        category_id = data.get('category_id')
        description = data.get('description')
        price = data.get('price')

        if name is not None:
            item.name = name
        if category_id is not None:
            item.category_id = category_id
        if description is not None:
            item.description = description
        if price is not None:
            item.price = price

        try:
            db.session.commit()
            log_item(item, user.id, 'Modify MenuItem')
            return jsonify(item.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Item not found"}), 404


@menu_management_blueprint.route('/get_items', methods=['GET'])
def get_items():
    """
    Retrieves all menu items.

    This endpoint handles GET requests to fetch all menu items.

    Returns:
        - JSON response with a list of menu items and status code 200 on success.
        - JSON response with error message and status code 500 on server error.
    """
    items = MenuItem.query.filter(MenuItem.id != -1, MenuItem.id != 0).all()
    return jsonify([item.to_dict() for item in items]), 200


@menu_management_blueprint.route('/get_item/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """
    Retrieves a specific menu item by its ID.

    This endpoint handles GET requests to fetch a single menu item identified by 'item_id'.

    Parameters:
        - item_id (int): The ID of the menu item to retrieve.

    Returns:
        - JSON response with menu item details and status code 200 if found.
        - JSON response with error message and status code 404 if the item is not found.
    """
    item = MenuItem.query.get(item_id)
    if item:
        return jsonify(item.to_dict()), 200
    else:
        return jsonify({"msg": "Reservation not found"}), 404


@menu_management_blueprint.route('/get_items_by_category/<int:category_id>', methods=['GET'])
def get_items_by_category(category_id):
    """
    Retrieves menu items by their category ID.

    This endpoint handles GET requests to fetch menu items belonging to a specific category.

    Parameters:
        - category_id (int): The ID of the category for which items are to be retrieved.

    Returns:
        - JSON response with a list of menu items for the given category and status code 200 on success.
        - JSON response with error message and status code 404 if no items are found for the category.
    """
    items = MenuItem.query.filter_by(category_id=category_id).filter(MenuItem.id != -1, MenuItem.id != 0).all()
    if items:
        return jsonify([item.to_dict() for item in items]), 200
    else:
        return jsonify({"msg": "No items found for the given category ID"}), 404


# Balance management routes...
@menu_management_blueprint.route('/create_balance_entry', methods=['POST'])
def create_balance_entry():
    """
    Creates a new balance entry.

    This endpoint handles POST requests to add a new balance entry.
    It's used for recording transactions related to menu items or payments.

    Returns:
        - JSON response with the created balance entry and status code 201 on success.
        - JSON response with error message and status code 400 if required data is missing.
        - JSON response with error message and status code 500 on server error.
    """

    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    data = request.get_json()
    reservation_id = data.get('reservation_id')
    menu_item_id = data.get('menu_item_id', 0)  # Default 0 for payment
    amount = data.get('amount', 0)  # Default amount to 0
    number_of_items = data.get('number_of_items', 1)  # Default number of items to 1

    if reservation_id is None:
        return jsonify({"msg": "Missing required balance data"}), 400

    new_balance_entry = Balance(
        reservation_id=reservation_id,
        menu_item_id=menu_item_id,
        amount=amount,
        number_of_items=number_of_items)

    try:
        db.session.add(new_balance_entry)
        db.session.commit()

        # Determine the action type
        action = "Add"
        # Log the action with balance entry
        log_balance_entry(new_balance_entry, user.id, action)

        return jsonify(new_balance_entry.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


@menu_management_blueprint.route('/get_balance_entries', methods=['GET'])
# @jwt_required()
# @requires_roles('Admin', 'Manager', 'Bar', 'Reception')
def get_balance_entries():
    """
    Retrieves all balance entries.

    This endpoint handles GET requests to fetch all balance entries.
    It is typically used for administrative and management purposes.

    Returns:
        - JSON response with a list of balance entries and status code 200 on success.
        - JSON response with error message and status code 500 on server error.
    """
    balance_entries = Balance.query.all()
    return jsonify([entry.to_dict() for entry in balance_entries]), 200


@menu_management_blueprint.route('/get_balance_entries/<int:reservation_id>', methods=['GET'])
# @jwt_required()
# @requires_roles('Admin', 'Manager', 'Bar', 'Reception')
def get_balance_entries_for_reservation(reservation_id):
    """
    Retrieves balance entries for a specific reservation.

    This endpoint handles GET requests to fetch balance entries associated with a given reservation ID.

    Parameters:
        - reservation_id (int): The ID of the reservation for which balance entries are to be retrieved.

    Returns:
        - JSON response with a list of balance entries for the reservation and status code 200 on success.
        - JSON response with error message and status code 404 if no entries are found for the reservation.
    """
    balance_entries = Balance.query.filter_by(reservation_id=reservation_id).all()
    if balance_entries:
        return jsonify([entry.to_dict() for entry in balance_entries]), 200
    else:
        return jsonify({"msg": "No balance entries found for the given reservation ID"}), 404


@menu_management_blueprint.route('/remove_balance_entry/<int:balance_entry_id>', methods=['DELETE'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def remove_balance_entry(balance_entry_id):
    """
    Deletes a balance entry.

    This endpoint handles DELETE requests to remove a specific balance entry identified by 'balance_entry_id'.

    Parameters:
        - balance_entry_id (int): The ID of the balance entry to be removed.

    Returns:
        - JSON response with success message and status code 200 on successful deletion.
        - JSON response with error message and status code 404 if the balance entry is not found.
        - JSON response with error message and status code 500 on server error.
    """

    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    balance_entry = Balance.query.get(balance_entry_id)
    if balance_entry:
        try:
            db.session.delete(balance_entry)
            db.session.commit()

            # Determine the action type
            action = "Delete"

            # Log the action with balance entry ID
            log_balance_entry(balance_entry, user.id, action)
            return jsonify({"msg": "Balance entry removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Balance entry not found"}), 404


@menu_management_blueprint.route('/modify_balance_entry/<int:balance_entry_id>', methods=['PUT'])
# @jwt_required()
# @requires_roles('Admin', 'Manager')
def modify_balance_entry(balance_entry_id):
    """
    Modifies an existing balance entry.

    This endpoint handles PUT requests to update details of a specific balance entry identified by 'balance_entry_id'.

    Parameters:
        - balance_entry_id (int): The ID of the balance entry to be modified.

    Returns:
        - JSON response with the updated balance entry details and status code 200 on success.
        - JSON response with error message and status code 404 if the balance entry is not found.
        - JSON response with error message and status code 500 on server error.
    """

    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    balance_entry = Balance.query.get(balance_entry_id)
    if balance_entry:
        data = request.get_json()
        reservation_id = data.get('reservation_id')
        menu_item_id = data.get('menu_item_id')
        amount = data.get('amount')

        if reservation_id is not None:
            balance_entry.reservation_id = reservation_id
        if menu_item_id is not None:
            balance_entry.menu_item_id = menu_item_id
        if amount is not None:
            balance_entry.amount = amount

        try:
            db.session.commit()
            # Determine the action type
            action = "Modify"

            # Log the action with balance entry ID
            log_balance_entry(balance_entry, user.id, action)

            return jsonify(balance_entry.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            print(e)
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Balance entry not found"}), 404


@menu_management_blueprint.route('/add_payment', methods=['POST'])
# @jwt_required()
# @requires_roles('Admin', 'Manager', 'Reception', 'Bar')
def add_payment():
    """
    Adds a payment as a balance entry.

    This endpoint handles POST requests to record a payment against a specific reservation.
    It requires details like reservation ID, payment amount, and payment method.

    Returns:
        - JSON response with the created balance entry and status code 201 on success.
        - JSON response with error message and status code 400 if required data is missing or invalid.
        - JSON response with error message and status code 500 on server error.
    """
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    user = User.query.get(6)  # TODO: Remove this line (debugging only)

    data = request.get_json()
    reservation_id = data.get('reservation_id')
    payment_amount = data.get('payment_amount')
    payment_method = data.get('payment_method')  # "cash" or "card"

    # Check for valid reservation ID, payment amount, and payment method
    if reservation_id is None or payment_amount is None or payment_method not in ["CASH",
                                                                                  "CARD"] or payment_amount == 0:
        return jsonify({"msg": "Missing or invalid payment data"}), 400

    try:
        # Ensure the payment amount is positive
        payment_amount = abs(float(payment_amount))

        # Convert the payment amount to a negative value for balance entry
        payment_amount = -payment_amount

        # Determine menu_item_id based on payment method
        menu_item_id = 0 if payment_method == "CASH" else -1

        # Create a new balance entry
        new_balance_entry = Balance(reservation_id=reservation_id, menu_item_id=menu_item_id, amount=payment_amount)

        db.session.add(new_balance_entry)
        db.session.commit()

        # Determine the action type
        action = "Add"

        # Log the action with balance entry
        log_balance_entry(new_balance_entry, user.id, action)

        return jsonify(new_balance_entry.to_dict()), 201
    except ValueError:
        return jsonify({"error": "Invalid payment amount"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def log_balance_entry(balance_entry, user_id, action):
    menu_item = MenuItem.query.get(balance_entry.menu_item_id)
    reservation = Reservation.query.get(balance_entry.reservation_id)
    room = Room.query.get(reservation.room_id)
    guest = Guest.query.get(reservation.guest_id)
    details = ""

    if menu_item.id > 0:
        action += " Order"
        details = f"Entry: {balance_entry.id} | " \
                  f"Reservation: {reservation.id} | " \
                  f"Room: {room.room_name} | " \
                  f"Guest: {guest.name} {guest.surname} | " \
                  f"Item: {menu_item.name} | " \
                  f"Quantity: {balance_entry.number_of_items} | " \
                  f"Price: {balance_entry.amount / balance_entry.number_of_items} | " \
                  f"Total: {balance_entry.amount}"

    else:
        payment_method = "Cash" if menu_item.id == 0 else "Card"

        action += " Payment"
        details = f"Entry: {balance_entry.id} | " \
                  f"Reservation: {reservation.id} | " \
                  f"Room: {room.room_name} | " \
                  f"Guest: {guest.name} {guest.surname} | " \
                  f"Payment Method: {payment_method} | " \
                  f"Paid: {balance_entry.amount}"

    logs.log_action(user_id, action, details)


def log_item(menu_item, user_id, action):
    category = MenuCategory.query.get(menu_item.category_id)
    details = f"ID: {menu_item.id} | " \
              f"Item: {menu_item.name} | " \
              f"Price: {menu_item.price} | " \
              f"Category: {category.name} | " \
              f"Description: {menu_item.description}"

    logs.log_action(user_id, action, details)


def log_category(category, user_id, action):
    details = f"Category: {category.name}"

    logs.log_action(user_id, action, details)
