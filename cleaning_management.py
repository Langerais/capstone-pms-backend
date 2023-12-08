from flask import jsonify, request, Blueprint
from datetime import datetime, timedelta

import room_management
from models import db, CleaningSchedule, CleaningAction, Room, Reservation  # Assuming these are your SQLAlchemy models

cleaning_management_blueprint = Blueprint('cleaning_management', __name__)


@cleaning_management_blueprint.route('/get_cleaning_schedule', methods=['GET'])
def get_cleaning_schedule():
    schedule = CleaningSchedule.query.all()
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/room/<int:room_id>', methods=['GET'])
def get_room_cleaning_schedule(room_id):
    schedule = CleaningSchedule.query.filter_by(room_id=room_id).all()
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/date_range', methods=['GET'])
def get_date_range_cleaning_schedule():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    schedule = CleaningSchedule.query.filter(CleaningSchedule.scheduled_date.between(start_date, end_date)).all()
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/room/<int:room_id>/date_range', methods=['GET'])
def get_room_date_range_cleaning_schedule(room_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    schedule = CleaningSchedule.query.filter(
        CleaningSchedule.room_id == room_id,
        CleaningSchedule.scheduled_date.between(start_date, end_date)
    ).all()
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_room_cleaning_schedule_by_date', methods=['GET'])
def get_room_cleaning_schedule_by_date():
    room_id = request.args.get('room_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Convert start_date and end_date to Python datetime objects if needed
    # For example, if dates are passed as 'YYYY-MM-DD' strings
    # start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    # end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Ensure all parameters are provided
    if not all([room_id, start_date, end_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Fetch the cleaning schedule for the specified room and date range
    schedule = CleaningSchedule.query.filter(
        CleaningSchedule.room_id == room_id,
        CleaningSchedule.scheduled_date.between(start_date, end_date)
    ).all()

    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule_for_reservations_date_range', methods=['GET'])
def get_cleaning_schedule_for_reservations_date_range():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start date and end date are required"}), 400

    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Get reservations in the date range
        reservations = Reservation.query.filter(Reservation.start_date <= end_date,
                                                Reservation.end_date >= start_date).all()
        room_ids = {reservation.room_id for reservation in reservations}

        # Get cleaning schedules for each room
        room_schedules = {}
        for room_id in room_ids:
            schedule = CleaningSchedule.query.filter(
                CleaningSchedule.room_id == room_id,
                CleaningSchedule.scheduled_date.between(start_date, end_date)
            ).all()
            room_schedules[room_id] = [entry.to_dict() for entry in schedule]

        return jsonify(room_schedules), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/remove_cleaning_task/<int:task_id>', methods=['DELETE'])
def remove_cleaning_task(task_id):
    task = CleaningSchedule.query.get(task_id)
    if not task:
        return jsonify({"error": "Cleaning task not found"}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Cleaning task removed successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/mark_task_completed', methods=['POST'])
def mark_task_completed():
    data = request.get_json()
    task_id = data.get('task_id')
    completed_date = data.get('completed_date')
    task_status = data.get('task_status')

    if not task_id or not completed_date:
        return jsonify({"error": "Task ID and completed date are required"}), 400

    try:
        completed_date = datetime.strptime(completed_date, '%Y-%m-%d').date()

        # Fetch the task and mark it as completed
        task = CleaningSchedule.query.get(task_id)
        if not task:
            return jsonify({"error": "Cleaning task not found"}), 404

        # task.status = 'completed'
        task.performed_timestamp = datetime.utcnow()
        db.session.commit()

        # Now reschedule future tasks for the same room and cleaning action
        reschedule_response = reschedule_future_tasks(task.room_id, task.action_id, completed_date)
        if reschedule_response.status_code != 200:
            raise Exception(reschedule_response.json()['error'])

        return jsonify({"message": "Task marked as completed and future tasks rescheduled"}), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Schedule cleaning for a single room
@cleaning_management_blueprint.route('/schedule_room_cleaning', methods=['POST'])
def schedule_room_cleaning():
    data = request.get_json()
    room_id = data.get('room_id')
    start_date = data.get('start_date')
    days = data.get('days', 7)  # Default to 7 days if not specified

    if not start_date:
        return jsonify({"error": "Start date is required"}), 400

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        room = room_management.get_room(room_id)
        success, error = schedule_room_cleaning_for(room.id, start_date, days)
        if error:
            raise Exception(error['error'])

        return jsonify({"message": "Cleaning scheduled successfully for all rooms"}), 200
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# Schedule cleaning for all rooms
@cleaning_management_blueprint.route('/schedule_cleaning', methods=['POST'])
def schedule_cleaning():
    data = request.get_json()
    start_date = data.get('start_date')
    days = data.get('days', 7)

    if not start_date:
        return jsonify({"error": "Start date is required"}), 400

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        rooms = Room.query.all()

        for room in rooms:
            success, error = schedule_room_cleaning_for(room.id, start_date, days)
            if error:
                raise Exception(error['error'])

        return jsonify({"message": "Cleaning scheduled successfully for all rooms"}), 200
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def schedule_room_cleaning_for(room_id, start_date, days):
    try:
        cleaning_actions = CleaningAction.query.all()
        room = Room.query.get(room_id)

        if not room:
            return {"error": "Room not found"}, None

        # Fetch reservations for this room in the given date range
        reservations = Reservation.query.filter(
            Reservation.room_id == room.id,
            Reservation.end_date >= start_date,
            Reservation.start_date <= start_date + timedelta(days=days)
        ).order_by(Reservation.start_date).all()

        for reservation in reservations:
            check_in_date = reservation.start_date
            check_out_date = reservation.end_date

            # Schedule cleaning for each day of the stay
            current_date = check_in_date
            while current_date <= check_out_date:
                for action in cleaning_actions:
                    # Schedule cleaning task for each day of stay, based on action frequency
                    if (current_date - check_in_date).days % action.frequency_days == 0 or current_date == check_out_date:
                        new_schedule = CleaningSchedule(
                            room_id=room.id,
                            action_id=action.id,
                            scheduled_date=current_date,
                            performed_timestamp=None
                        )
                        db.session.add(new_schedule)

                current_date += timedelta(days=1)

        db.session.commit()
        return {"message": f"Cleaning scheduled for Room {room_id} successfully"}, None
    except ValueError as e:
        return None, {"error": "Invalid date format. Please use YYYY-MM-DD"}
    except Exception as e:
        db.session.rollback()
        return None, {"error": str(e)}



@cleaning_management_blueprint.route('/reschedule_future_tasks', methods=['POST'])
def reschedule_future_tasks(room_id, action_id,
                            completed_date):  # Reschedule future tasks for a room and cleaning action if a task is completed early
    data = request.get_json()
    room_id = data.get('room_id')
    action_id = data.get('action_id')
    completed_date = data.get('completed_date')

    if not all([room_id, action_id, completed_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        completed_date = datetime.strptime(completed_date, '%Y-%m-%d').date()

        # Fetch the cleaning action's frequency
        action = CleaningAction.query.get(action_id)
        if not action:
            return jsonify({"error": "Cleaning action not found"}), 404

        frequency_days = action.frequency_days

        # Fetch all future tasks for the same room and action
        future_tasks = CleaningSchedule.query.filter(
            CleaningSchedule.room_id == room_id,
            CleaningSchedule.action_id == action_id,
            CleaningSchedule.scheduled_date > completed_date
        ).order_by(CleaningSchedule.scheduled_date).all()

        # Reschedule each future task
        new_scheduled_date = completed_date
        for task in future_tasks:
            new_scheduled_date = _find_next_available_date(new_scheduled_date, frequency_days, room_id, action_id)
            if new_scheduled_date != task.scheduled_date:
                task.scheduled_date = new_scheduled_date
            else:
                # If the task is the same for the same room on the same date, remove it
                db.session.delete(task)

        db.session.commit()
        return jsonify({"message": "Future tasks rescheduled successfully"}), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def _find_next_available_date(start_date, frequency_days, room_id, action_id):
    """Find the next available date for scheduling, skipping dates with conflicts."""
    new_date = start_date
    while True:
        new_date += timedelta(days=frequency_days)
        existing_task = CleaningSchedule.query.filter(
            CleaningSchedule.room_id == room_id,
            CleaningSchedule.action_id == action_id,
            CleaningSchedule.scheduled_date == new_date
        ).first()
        if not existing_task:
            break
    return new_date


@cleaning_management_blueprint.route('/get_cleaning_actions', methods=['GET'])
def get_cleaning_actions():
    try:
        print("get cleaning actions")
        actions = CleaningAction.query.all()
        print("got cleaning actions")
        return jsonify([action.to_dict() for action in actions]), 200
    except Exception as e:
        print("Exception occurred:", e)
        return jsonify({'error': str(e)}), 500

