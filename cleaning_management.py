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

    if not start_date:
        return jsonify({"error": "Start date is required"}), 400

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        rooms = Room.query.all()

        for room in rooms:
            success, error = schedule_room_cleaning_for(room.id, start_date)
            if error:
                raise Exception(error['error'])

        return jsonify({"message": "Cleaning scheduled successfully for all rooms"}), 200
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


# Helper function to schedule cleaning for a single room for a specified date
def schedule_room_cleaning_for(room_id, date_to_schedule):
    try:
        # Ensure date_to_schedule is a date object
        if isinstance(date_to_schedule, datetime):
            date_to_schedule = date_to_schedule.date()

        # Delete existing tasks for this room on the specified date
        CleaningSchedule.query.filter(
            CleaningSchedule.room_id == room_id,
            CleaningSchedule.scheduled_date == date_to_schedule
        ).delete()

        cleaning_actions = CleaningAction.query.all()
        room = Room.query.get(room_id)
        if not room:
            return {"error": "Room not found"}, None

        max_frequency = max(action.frequency_days for action in cleaning_actions)
        check_start_date = date_to_schedule - timedelta(days=max_frequency + 1)

        recent_or_pending_tasks = CleaningSchedule.query.filter(
            CleaningSchedule.room_id == room_id,
            CleaningSchedule.scheduled_date.between(check_start_date, date_to_schedule - timedelta(days=1)),
        ).all()

        recent_or_pending_tasks_dict = {task.action_id: task for task in recent_or_pending_tasks}

        # Check for departure on the date_to_schedule
        is_departure_today = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.end_date == date_to_schedule
        ).count() > 0

        if is_departure_today or not recent_or_pending_tasks:
            for action in cleaning_actions:
                schedule_cleaning_task(room.id, action.id, date_to_schedule, 'pending')
        else:
            for action in cleaning_actions:
                last_completed_or_scheduled = recent_or_pending_tasks_dict.get(action.id)
                if should_schedule_task(last_completed_or_scheduled, action.frequency_days, date_to_schedule):
                    schedule_cleaning_task(room.id, action.id, date_to_schedule, 'pending')

        db.session.commit()
        return {"message": f"Cleaning tasks scheduled for Room {room_id} on {date_to_schedule}"}, None
    except Exception as e:
        db.session.rollback()
        return None, {"error": str(e)}

def schedule_cleaning_task(room_id, action_id, scheduled_date, status):
    new_task = CleaningSchedule(
        room_id=room_id,
        action_id=action_id,
        scheduled_date=scheduled_date,
        status=status
    )
    db.session.add(new_task)

def should_schedule_task(last_task, frequency, target_date):
    if last_task is None or last_task.status == 'pending':
        return True
    return (target_date - last_task.scheduled_date).days >= frequency




@cleaning_management_blueprint.route('/toggle_task_status/<int:id>', methods=['POST'])
def change_task_status(id):
    data = request.get_json()
    task_status = data.get('task_status')
    completed_date_str = data.get('completed_date')

    if not id or not completed_date_str:
        return jsonify({"error": "Task ID and completed date are required"}), 400

    try:
        # Properly parse the datetime string
        #completed_date = datetime.strptime(completed_date_str, '%Y-%m-%d %H:%M')

        task = CleaningSchedule.query.get(id)
        if not task:
            return jsonify({"error": "Cleaning task not found"}), 404

        task.status = task_status
        task.performed_timestamp = datetime.utcnow() if task_status == 'completed' else None

        reschedule_message, reschedule_status_code = reschedule_future_tasks_helper(task.room_id, task.action_id, completed_date_str)
        if reschedule_status_code != 200:
            db.session.rollback()
            return jsonify(reschedule_message), reschedule_status_code

        db.session.commit()
        return jsonify({"message": "Task marked as completed and future tasks rescheduled"}), 200

    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD HH:MM"}), 400
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500




def reschedule_future_tasks_helper(room_id, action_id, completed_date):

    if not all([room_id, action_id, completed_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    try:
        completed_date = datetime.strptime(completed_date, '%Y-%m-%d %H:%M').date()

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
        return {"message": "Future tasks rescheduled successfully"}, 200

    except Exception as e:
        db.session.rollback()
        print(e)
        return {"error": str(e)}, 500


# Flask route that uses the helper function
@cleaning_management_blueprint.route('/reschedule_future_tasks', methods=['POST'])
def reschedule_future_tasks():
    data = request.get_json()
    room_id = data.get('room_id')
    action_id = data.get('action_id')
    completed_date = data.get('completed_date')

    # Validate inputs
    if not all([room_id, action_id, completed_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    message, status_code = reschedule_future_tasks_helper(room_id, action_id, completed_date)
    return jsonify(message), status_code

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
