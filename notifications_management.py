from datetime import datetime

from flask import Blueprint, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler

import logs
from models import Room, Reservation, Guest, Balance, AppNotification, db, User

notifications_management_blueprint = Blueprint('notifications_management', __name__)


# Example of a scheduled task to generate and send notifications
def generate_daily_notifications():
    # Logic to generate notifications
    pass

    scheduler = BackgroundScheduler()
    scheduler.add_job(generate_daily_notifications, 'cron', hour=5)  # Run daily at 9 AM
    scheduler.start()


@notifications_management_blueprint.route('/get_notifications', methods=['GET'])
def get_notifications():
    try:
        # Fetch all notifications, or add filters as per your requirement
        notifications = AppNotification.query.all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@notifications_management_blueprint.route('/get_notifications/<int:notification_id>', methods=['GET'])
def get_notification(notification_id):
    try:
        notification = AppNotification.query.filter_by(id=notification_id).first()
        if notification:
            return jsonify(notification.to_dict()), 200
        else:
            return jsonify({'error': 'Notification not found'}), 404
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


# Get notifications for a department
@notifications_management_blueprint.route('/get_notifications/department/<string:department>', methods=['GET'])
def get_notifications_for_department(department):
    try:
        notifications = AppNotification.query.filter_by(department=department).all()
        return jsonify([notification.to_dict() for notification in notifications]), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500


@notifications_management_blueprint.route('/add_notification', methods=['POST'])
def create_notification():
    ##current_user_email = get_jwt_identity()  # Get the user's email from the token
    ##user = User.query.filter_by(email=current_user_email).first()
    manager = User.query.get(6)  # TODO: Remove this line (debugging only)

    try:
        data = request.json
        new_notification = AppNotification(
            title=data['title'],
            message=data['message'],
            department=data['department'],
            priority=data['priority'],
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%dT%H:%M:%S')
        )
        db.session.add(new_notification)
        db.session.commit()
        log_notification(new_notification, manager, "Create Notification")
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def log_notification(notification, user_id, action):
    """
    Log notification-related actions and details.

    Args:
        notification (AppNotification): The notification entity for which the action is being logged.
        user_id (int): The ID of the user involved in the action.
        action (str): The action being performed, such as "Create Notification" or "Modify Notification".

    Logs the details of the action along with notification information.

    Example of logged details:
    "ID: 4 | Title: New Notification | Message: This is a new notification | Department: IT | Priority: 1 | Expiry Date: 2021-01-01 00:00:00"

    The logged information can be used for auditing and tracking notification-related activities.

    Returns:
        None
    """
    details = f"ID: {notification.id} |" \
              f"Title: {notification.title} | " \
              f"Message: {notification.message} | " \
              f"Department: {notification.department} | " \
              f"Priority: {notification.priority} | " \
              f"Expiry Date: {notification.expiry_date}"

    logs.log_action(user_id, action, details)
