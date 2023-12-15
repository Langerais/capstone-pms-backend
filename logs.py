from flask import Blueprint, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Reservation, Balance, User  # Import the Reservation model from models.py


logging_blueprint = Blueprint('logging', __name__)


class UserActionLog(db.Model):
    __tablename__ = 'user_actions_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True, default=None)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, action, details=None):
        self.user_id = user_id
        self.action = action
        self.details = details


def log_action(user_id, action, details=None):
    # Create a new log entry using the UserActionLog model
    new_log = UserActionLog(
        #user_id=user_id,
        user_id=6,  # TODO: Remove this hard-coded value and uncomment the line above (after testing)
        action=action,
        details=details,
    )

    # Add the new log entry to the database and commit the changes
    try:
        db.session.add(new_log)
        db.session.commit()
    except Exception as e:
        # Handle exceptions such as database errors
        db.session.rollback()
        print("Failed to log action:", e)


@logging_blueprint.route('/get_logs', methods=['GET'])
def get_all_logs():
    logs = UserActionLog.query.all()
    return jsonify([log.to_dict() for log in logs]), 200


@logging_blueprint.route('/user/<int:user_id>', methods=['GET'])
def get_logs_for_user(user_id):
    logs = UserActionLog.query.filter_by(user_id=user_id).all()
    return jsonify([log.to_dict() for log in logs]), 200


@logging_blueprint.route('/action/<string:action>', methods=['GET'])
def get_logs_for_action(action):
    logs = UserActionLog.query.filter_by(action=action).all()
    return jsonify([log.to_dict() for log in logs]), 200


@logging_blueprint.route('/user/<int:user_id>/action/<string:action>', methods=['GET'])
def get_logs_for_user_and_action(user_id, action):
    logs = UserActionLog.query.filter_by(user_id=user_id, action=action).all()
    return jsonify([log.to_dict() for log in logs]), 200


@logging_blueprint.route('/actions', methods=['GET'])
def get_unique_actions():
    unique_actions = UserActionLog.query.with_entities(UserActionLog.action).distinct()
    actions = [action.action for action in unique_actions]
    return jsonify(actions), 200
