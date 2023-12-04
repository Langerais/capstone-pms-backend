from decimal import Decimal

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from auth import requires_roles
from models import db, MenuCategory, MenuItem, Balance  # Assuming models are defined in models.py
from datetime import datetime

menu_management_blueprint = Blueprint('menu_management', __name__)


# Category management
@menu_management_blueprint.route('/create_category', methods=['POST'])
def create_category():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"msg": "Missing category name"}), 400

    new_category = MenuCategory(name=name)

    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@menu_management_blueprint.route('/remove_category/<int:category_id>', methods=['DELETE'])
def remove_category(category_id):
    category = MenuCategory.query.get(category_id)
    if category:
        try:
            db.session.delete(category)
            db.session.commit()
            return jsonify({"msg": "Category removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Category not found"}), 404


@menu_management_blueprint.route('/modify_category/<int:category_id>', methods=['PUT'])
def modify_category(category_id):
    category = MenuCategory.query.get(category_id)
    if category:
        data = request.get_json()
        name = data.get('name')
        if name is not None:
            category.name = name

        try:
            db.session.commit()
            return jsonify(category.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Category not found"}), 404



@menu_management_blueprint.route('/get_categories', methods=['GET'])
def get_categories():  # TESTED OK
    categories = MenuCategory.query.all()
    return jsonify([category.to_dict() for category in categories]), 200


# Menu item management
@menu_management_blueprint.route('/create_item', methods=['POST'])
def create_item():  # TESTED OK
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
        return jsonify(new_item.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@menu_management_blueprint.route('/remove_item/<int:item_id>', methods=['DELETE'])
def remove_item(item_id):
    item = MenuItem.query.get(item_id)
    if item:
        try:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"msg": "Item removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Item not found"}), 404


@menu_management_blueprint.route('/modify_item/<int:item_id>', methods=['PUT'])
def modify_item(item_id):
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
            return jsonify(item.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Item not found"}), 404


@menu_management_blueprint.route('/get_items', methods=['GET'])
def get_items(): # TESTED OK
    items = MenuItem.query.all()
    return jsonify([item.to_dict() for item in items]), 200\



@menu_management_blueprint.route('/get_item', methods=['GET'])
def get_menu_item(item_id): # TESTED OK
    item = MenuItem.query.get(item_id)
    if item:
        return jsonify(item.to_dict()), 200
    else:
        return jsonify({"msg": "Reservation not found"}), 404


@menu_management_blueprint.route('/get_items_by_category/<int:category_id>', methods=['GET'])
def get_items_by_category(category_id): # TESTED OK
    items = MenuItem.query.filter_by(category_id=category_id).all()
    if items:
        return jsonify([item.to_dict() for item in items]), 200
    else:
        return jsonify({"msg": "No items found for the given category ID"}), 404


# Balance management
@menu_management_blueprint.route('/create_balance_entry', methods=['POST'])
def create_balance_entry(): # TESTED OK
    data = request.get_json()
    reservation_id = data.get('reservation_id')
    menu_item_id = data.get('menu_item_id', 0)  # Default 0 for payment
    amount = data.get('amount', 0)  # Default amount to 0
    number_of_items = data.get('number_of_items', 1)  # Default number of items to 1

    if reservation_id is None:
        return jsonify({"msg": "Missing required balance data"}), 400

    new_balance_entry = Balance(reservation_id=reservation_id, menu_item_id=menu_item_id, amount=amount, number_of_items=number_of_items)

    try:
        db.session.add(new_balance_entry)
        db.session.commit()
        return jsonify(new_balance_entry.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@menu_management_blueprint.route('/get_balance_entries', methods=['GET'])
def get_balance_entries():
    balance_entries = Balance.query.all()
    return jsonify([entry.to_dict() for entry in balance_entries]), 200


@menu_management_blueprint.route('/get_balance_entries/<int:reservation_id>', methods=['GET'])
def get_balance_entries_for_reservation(reservation_id):
    balance_entries = Balance.query.filter_by(reservation_id=reservation_id).all()
    if balance_entries:
        return jsonify([entry.to_dict() for entry in balance_entries]), 200
    else:
        return jsonify({"msg": "No balance entries found for the given reservation ID"}), 404


@menu_management_blueprint.route('/remove_balance_entry/<int:balance_entry_id>', methods=['DELETE'])
@jwt_required()
@requires_roles('Admin')
def remove_balance_entry(balance_entry_id):
    balance_entry = Balance.query.get(balance_entry_id)
    if balance_entry:
        try:
            db.session.delete(balance_entry)
            db.session.commit()
            return jsonify({"msg": "Balance entry removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Balance entry not found"}), 404


@jwt_required()
@requires_roles('Admin')
@menu_management_blueprint.route('/modify_balance_entry/<int:balance_entry_id>', methods=['PUT'])
def modify_balance_entry(balance_entry_id):
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
            return jsonify(balance_entry.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Balance entry not found"}), 404


@menu_management_blueprint.route('/add_payment', methods=['POST'])
def add_payment():  # Guest payment
    data = request.get_json()
    reservation_id = data.get('reservation_id')
    payment_amount = data.get('payment_amount')
    payment_method = data.get('payment_method')  # "cash" or "card"

    # Check for valid reservation ID, payment amount, and payment method
    if reservation_id is None or payment_amount is None or payment_method not in ["cash", "card"]:
        return jsonify({"msg": "Missing or invalid payment data"}), 400

    try:
        # Ensure the payment amount is positive
        payment_amount = abs(float(payment_amount))

        # Convert the payment amount to a negative value for balance entry
        payment_amount = -payment_amount

        # Determine menu_item_id based on payment method
        menu_item_id = 0 if payment_method == "cash" else -1

        # Create a new balance entry
        new_balance_entry = Balance(reservation_id=reservation_id, menu_item_id=menu_item_id, amount=payment_amount)

        db.session.add(new_balance_entry)
        db.session.commit()
        return jsonify(new_balance_entry.to_dict()), 201
    except ValueError:
        return jsonify({"error": "Invalid payment amount"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


