import pytz
from flask import Blueprint, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Reservation, Balance, User  # Import the Reservation model from models.py
from sqlalchemy import and_, or_

logging_blueprint = Blueprint('logging', __name__)


class UserActionLog(db.Model):
    __tablename__ = 'user_actions_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True, default=None)
    timestamp = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, user_id, action, details=None):
        self.user_id = user_id
        self.action = action
        self.details = details
        self.timestamp = datetime.now(pytz.timezone('Europe/Athens'))

    def to_dict(self):
        """Convert the UserActionLog object to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


def log_action(user_id, action, details=None):
    # Create a new log entry using the UserActionLog model
    new_log = UserActionLog(
        user_id=user_id,
        # user_id=6,  # TODO: Remove this hard-coded value
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


# Get logs for a date range
@logging_blueprint.route('/date_range/<string:start_date>/<string:end_date>', methods=['GET'])
def get_logs_for_date_range(start_date, end_date):
    # Convert the date strings into datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Get the logs for the date range
    logs = UserActionLog.query.filter(UserActionLog.timestamp >= start_date, UserActionLog.timestamp <= end_date).all()
    return jsonify([log.to_dict() for log in logs]), 200


# Get logs for user and date range
@logging_blueprint.route('/user/<int:user_id>/date_range/<string:start_date>/<string:end_date>', methods=['GET'])
def get_logs_for_user_and_date_range(user_id, start_date, end_date):
    # Convert the date strings into datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Get the logs for the date range
    logs = UserActionLog.query.filter(UserActionLog.timestamp >= start_date, UserActionLog.timestamp <= end_date,
                                      UserActionLog.user_id == user_id).all()
    return jsonify([log.to_dict() for log in logs]), 200


@logging_blueprint.route('/search_logs', methods=['GET'])
def search_logs():
    # Get parameters from the request
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    action = request.args.get('action')
    user_id = request.args.get('user_id', type=int)
    details = request.args.get('details')

    # Convert dates to datetime objects
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%f')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S.%f')

    # Build the query
    query = UserActionLog.query

    if start_date and end_date:
        query = query.filter(UserActionLog.timestamp.between(start_date, end_date))

    if action and action != 'All Actions':
        query = query.filter(UserActionLog.action == action)

    if user_id and user_id > 0:
        query = query.filter(UserActionLog.user_id == user_id)

    if user_id == 0:
        query = query.filter(UserActionLog.user_id == user_id)




    if details:
        query = query.filter(UserActionLog.details.like(f'%{details}%'))

    # Execute the query
    logs = query.all()

    # Convert logs to a JSON serializable format
    logs_list = [log.to_dict() for log in logs]  # Ensure you have a to_dict method in your UserActionLog model

    #logs_for_system = query.filter(UserActionLog.user_id == 0).all()
    #print(logs_for_system)
   # for log in logs:
    #    print(log.to_dict())

    return jsonify(logs_list), 200
