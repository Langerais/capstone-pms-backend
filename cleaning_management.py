"""
This module defines Flask routes for managing cleaning schedules in a facility management application.
It includes routes for retrieving cleaning schedules, managing cleaning tasks, and handling related data.
"""

from flask import jsonify, request, Blueprint
from datetime import datetime, timedelta

from flask_jwt_extended import jwt_required, get_jwt_identity

import logs
import room_management
from auth import requires_roles
from models import db, CleaningSchedule, CleaningAction, Room, Reservation, \
    User  # Assuming these are your SQLAlchemy models

cleaning_management_blueprint = Blueprint('cleaning_management', __name__)


@cleaning_management_blueprint.route('/get_cleaning_schedule', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_cleaning_schedule():
    """
    Flask route to retrieve the entire cleaning schedule.

    This route handles a GET request to fetch all entries in the CleaningSchedule database.
    It's used to obtain a comprehensive view of all scheduled cleaning tasks.

    Returns:
    Flask Response: A JSON list of all cleaning schedules, each converted to a dictionary.
    """

    # Query the database to retrieve all cleaning schedule entries
    schedule = CleaningSchedule.query.all()

    # Convert each schedule entry to a dictionary and return them as a JSON list
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/room/<int:room_id>', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_room_cleaning_schedule(room_id):
    """
    Flask route to retrieve the cleaning schedule for a specific room.

    This route processes a GET request to fetch all cleaning schedules associated with a specific room,
    identified by 'room_id'. It's useful for viewing the cleaning tasks planned for a particular room.

    Parameters:
    room_id (int): The identifier of the room for which the schedule is requested.

    Returns:
    Flask Response: A JSON list of cleaning schedules for the specified room, each converted to a dictionary.
    """

    # Query the database to retrieve all cleaning schedule entries for the specified room
    schedule = CleaningSchedule.query.filter_by(room_id=room_id).all()

    # Convert each schedule entry to a dictionary and return them as a JSON list
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/date_range', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_date_range_cleaning_schedule():
    """
    Flask route to retrieve cleaning schedules within a specified date range.

    This route processes a GET request to obtain all cleaning schedules between two dates,
    as specified by 'start_date' and 'end_date' in the request's query parameters.

    Returns:
    Flask Response: A JSON list of cleaning schedules within the specified date range.
    """

    # Retrieve start and end dates from the request's query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query the database for cleaning schedules within the specified date range
    schedule = CleaningSchedule.query.filter(CleaningSchedule.scheduled_date.between(start_date, end_date)).all()

    # Convert the schedule entries to dictionaries and return them as JSON
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule/room/<int:room_id>/date_range', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_room_date_range_cleaning_schedule(room_id):
    """
    Flask route to retrieve the cleaning schedules for a specific room within a given date range.

    This route processes a GET request to fetch cleaning schedules for a specified room,
    determined by 'room_id', between two dates ('start_date' and 'end_date').

    Parameters:
    room_id (int): The identifier of the room for which the schedule is requested.

    Returns:
    Flask Response: A JSON list of cleaning schedules for the specified room within the given date range.
    """

    # Retrieve start and end dates from the request's query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query the database for cleaning schedules for the specified room in the date range
    schedule = CleaningSchedule.query.filter(
        CleaningSchedule.room_id == room_id,
        CleaningSchedule.scheduled_date.between(start_date, end_date)
    ).all()

    # Convert the schedule entries to dictionaries and return them as JSON
    return jsonify([entry.to_dict() for entry in schedule]), 200


def get_room_today_cleaning_schedule(room_id):
    # Query the database for cleaning schedules for the specified room in the date range
    schedule = CleaningSchedule.query.filter(
        CleaningSchedule.room_id == room_id,
        CleaningSchedule.scheduled_date.equal(datetime.now().date())
    ).all()

    # Convert the schedule entries to dictionaries and return them as JSON
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_room_cleaning_schedule_by_date', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_room_cleaning_schedule_by_date():
    """
    Flask route to obtain the cleaning schedule for a particular room over a specific date range.

    This route processes a GET request, extracting 'room_id', 'start_date', and 'end_date'
    from the query parameters to fetch the relevant cleaning schedules.

    Returns:
    Flask Response: A JSON list of cleaning schedules for the specified room and date range,
    or an error message if any required parameters are missing.
    """

    # Retrieve room ID and date range from query parameters
    room_id = request.args.get('room_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Ensure all required parameters are provided
    if not all([room_id, start_date, end_date]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Query for cleaning schedules within the specified parameters
    schedule = CleaningSchedule.query.filter(
        CleaningSchedule.room_id == room_id,
        CleaningSchedule.scheduled_date.between(start_date, end_date)
    ).all()

    # Return the schedules as JSON
    return jsonify([entry.to_dict() for entry in schedule]), 200


@cleaning_management_blueprint.route('/get_cleaning_schedule_for_reservations_date_range', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_cleaning_schedule_for_reservations_date_range():
    """
    Flask route to retrieve cleaning schedules linked to reservations within a certain date range.

    This route processes a GET request to fetch cleaning schedules for rooms that have reservations
    starting or ending between 'start_date' and 'end_date', as specified in the query parameters.

    Returns:
    Flask Response: A JSON object mapping room IDs to their respective cleaning schedules,
    or an error message if start and end dates are not provided.
    """

    # Retrieve start and end dates from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Ensure both start and end dates are provided
    if not start_date or not end_date:
        return jsonify({"error": "Start date and end date are required"}), 400

    try:
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Get reservations that either start or end within the specified date range
        reservations = Reservation.query.filter(
            Reservation.start_date <= end_date,
            Reservation.end_date >= start_date
        ).all()

        # Extract unique room IDs from these reservations
        room_ids = {reservation.room_id for reservation in reservations}

        # Fetch cleaning schedules for each room within the date range
        room_schedules = {}
        for room_id in room_ids:
            schedule = CleaningSchedule.query.filter(
                CleaningSchedule.room_id == room_id,
                CleaningSchedule.scheduled_date.between(start_date, end_date)
            ).all()
            room_schedules[room_id] = [entry.to_dict() for entry in schedule]

        # Return the compiled cleaning schedules as JSON
        return jsonify(room_schedules), 200

    except ValueError:
        # Handle invalid date format error
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        # Handle other exceptions and perform a database rollback
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/remove_cleaning_task/<int:task_id>', methods=['DELETE'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def remove_cleaning_task(task_id):
    """
    Flask route to delete a specific cleaning task from the schedule.

    This route processes a DELETE request to remove a cleaning task, identified by its 'task_id',
    from the CleaningSchedule database.

    Parameters:
    task_id (int): The identifier of the cleaning task to be removed.

    Returns:
    Flask Response: A success message if the task is deleted, or an error message if not found or in case of failure.
    """

    # Fetch the task from the database using the provided task ID
    task = CleaningSchedule.query.get(task_id)
    if not task:
        # Task not found in the database
        return jsonify({"error": "Cleaning task not found"}), 404

    try:
        # Delete the task and commit changes to the database
        db.session.delete(task)
        db.session.commit()
        return jsonify({"message": "Cleaning task removed successfully"}), 200
    except Exception as e:
        # Handle exceptions, rollback the transaction, and return an error message
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/schedule_room_cleaning', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager')
def schedule_room_cleaning():
    """
    Flask route to schedule cleaning for a specific room over a number of days.

    This route handles a POST request with JSON data containing room_id, start_date, and optionally the number of days
    for which the cleaning should be scheduled. It schedules cleaning tasks for the specified room starting from the
    given start_date and continuing for the specified number of days.

    Returns:
    Flask Response: A success message if scheduling is successful, or an error message in case of failure.
    """

    # Extract data from the JSON payload of the request
    data = request.get_json()
    room_id = data.get('room_id')
    start_date = data.get('start_date')
    days = data.get('days', 7)  # Default to 7 days if the 'days' parameter is not specified

    # Validate the presence of a start date
    if not start_date:
        return jsonify({"error": "Start date is required"}), 400

    try:
        # Convert the start date from string to datetime object
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

        # Fetch the room details and schedule cleaning
        room = room_management.get_room(room_id)
        success, error = schedule_room_cleaning_for(room.id, start_date)  # Removed 'days' parameter

        # Handle any errors during scheduling
        if error:
            raise Exception(error['error'])

        # Return a success message
        return jsonify({"message": "Cleaning scheduled successfully for room"}), 200

    except ValueError:
        # Handle invalid date format error
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        # Handle other exceptions and perform a database rollback
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/schedule_cleaning', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager')
def schedule_cleaning():
    """
    Flask route to schedule cleaning for all rooms starting from a given date.

    This route processes a POST request to schedule cleaning tasks for every room in the database starting from a
    specified start date. The data for the start date is provided in the JSON payload of the request.

    Returns:
    Flask Response: A success message if scheduling is successful for all rooms, or an error message in case of failure.
    """

    # Extract start date from the JSON payload of the request
    data = request.get_json()
    start_date = data.get('start_date')

    # Validate the presence of a start date
    if not start_date:
        return jsonify({"error": "Start date is required"}), 400

    try:
        # Convert the start date from string to datetime object
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

        # Fetch all rooms from the database
        rooms = Room.query.all()

        # Schedule cleaning for each room starting from the start date
        for room in rooms:
            success, error = schedule_room_cleaning_for(room.id, start_date)
            if error:
                raise Exception(error['error'])

        log_cleaning_for_day_scheduled(start_date)

        # Return a success message
        return jsonify({"message": "Cleaning scheduled successfully for all rooms"}), 200

    except ValueError:
        # Handle invalid date format error
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD"}), 400
    except Exception as e:
        # Handle other exceptions and perform a database rollback
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


def schedule_cleaning_internal():
    """
    Internal function to schedule cleaning for all rooms starting from a given date.

    This function schedules cleaning tasks for every room in the database starting from a specified start date.

    Returns: None
    """
    try:
        # Convert the start date from string to datetime object
        start_date = datetime.today().date()
        # Fetch all rooms from the database
        rooms = Room.query.all()

        # Schedule cleaning for each room starting from the start date
        for room in rooms:
            success, error = schedule_room_cleaning_for(room.id, start_date)
            if error:
                raise Exception(error['error'])

        log_cleaning_for_day_scheduled(start_date)
        print("Cleaning scheduled successfully for all rooms for date: ", start_date)

    except ValueError:
        # Handle invalid date format error
        print("Invalid date format. Please use YYYY-MM-DD")
    except Exception as e:
        # Handle other exceptions and perform a database rollback
        db.session.rollback()
        print(e)


def schedule_room_cleaning_for(room_id, date_to_schedule):
    """
    Schedules cleaning tasks for a specified room on a given date.

    This function schedules cleaning tasks based on room occupancy, check-in, and check-out dates.
    It ensures that tasks are scheduled according to the defined cleaning frequency and special conditions like
    check-out dates where full cleaning is mandatory.

    Parameters:
    room_id (int): The identifier for the room to be cleaned.
    date_to_schedule (datetime.date): The date for which cleaning tasks need to be scheduled.

    Returns:
    dict, None: A success message if scheduling is successful, or an error message in case of failure.
    """

    try:
        # Convert datetime to date if necessary
        if isinstance(date_to_schedule, datetime):
            date_to_schedule = date_to_schedule.date()

        # Fetch all cleaning actions and the specified room
        cleaning_actions = CleaningAction.query.all()
        room = Room.query.get(room_id)

        # Return an error if the room does not exist
        if not room:
            return {"error": "Room not found"}, None

        # Determine if there's a current reservation that includes the date_to_schedule
        current_reservation = Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.start_date <= date_to_schedule,
            Reservation.end_date >= date_to_schedule
        ).first()

        # Flag to check if there's a checkout happening on the date_to_schedule
        is_checkout_today = current_reservation and current_reservation.end_date == date_to_schedule

        # Clear any existing cleaning schedules for the specified date to avoid duplication
        CleaningSchedule.query.filter(
            CleaningSchedule.room_id == room_id,
            CleaningSchedule.scheduled_date == date_to_schedule
        ).delete()

        # If there's a checkout today, schedule a full cleaning
        if is_checkout_today:
            for action in cleaning_actions:
                schedule_cleaning_task(room.id, action.id, date_to_schedule, 'pending')

        # If the room is not currently reserved or if it's the check-in date
        elif not current_reservation or date_to_schedule == current_reservation.start_date:
            for action in cleaning_actions:
                if not was_task_performed(room_id, action.id, get_last_checkout_date_before(room_id, date_to_schedule),
                                          date_to_schedule):
                    schedule_cleaning_task(room.id, action.id, date_to_schedule, 'pending')

        # For occupied rooms (not on check-in date), schedule cleaning based on frequency
        elif current_reservation and date_to_schedule > current_reservation.start_date:
            for action in cleaning_actions:
                days_since_check_in = (date_to_schedule - current_reservation.start_date).days
                if days_since_check_in % action.frequency_days == 0 or not was_task_performed(
                        room_id, action.id, date_to_schedule - timedelta(days=action.frequency_days), date_to_schedule):
                    schedule_cleaning_task(room.id, action.id, date_to_schedule, 'pending')

        # Commit the changes to the database
        db.session.commit()
        return {"message": f"Cleaning scheduled for Room {room_id} on {date_to_schedule}"}, None
    except Exception as e:
        # Rollback in case of any exception
        db.session.rollback()
        return None, {"error": str(e)}


def schedule_cleaning_task(room_id, action_id, scheduled_date, status):
    """
    Creates a new cleaning task in the cleaning schedule.

    This function is used to add a specific cleaning task to the database for a room.
    It creates a new `CleaningSchedule` record with the given parameters.

    Parameters:
    room_id (int): The identifier for the room for which the task is scheduled.
    action_id (int): The identifier for the specific cleaning action to be performed.
    scheduled_date (datetime.date): The date on which the task is scheduled.
    status (str): The status of the cleaning task (e.g., 'pending').

    Returns:
    None: This function does not return anything. It adds a record to the database.
    """

    new_schedule = CleaningSchedule(
        room_id=room_id,
        action_id=action_id,
        scheduled_date=scheduled_date,
        status=status
    )
    # Add the new schedule to the session for committing
    db.session.add(new_schedule)


def was_task_performed(room_id, action_id, check_from_date, check_until_date):
    """
    Checks whether a specific cleaning task was performed for a room between two dates.

    This function iterates over each day from the last checkout date to a specified 'check until' date.
    It checks if a cleaning task identified by the action_id was completed for the specified room.

    Parameters:
    room_id (int): The identifier of the room.
    action_id (int): The identifier of the cleaning action to check.
    last_checkout_date (datetime.date): The starting date to check from (usually the last checkout date).
    check_until_date (datetime.date): The ending date to check until.

    Returns:
    bool: True if the task was completed at least once between the specified dates, False otherwise.
    """

    # Convert last_checkout_date and check_until_date to date objects if they are datetime instances
    if isinstance(check_from_date, datetime):
        check_from_date = check_from_date.date()
    if isinstance(check_until_date, datetime):
        check_until_date = check_until_date.date()

    # Iterate through each day within the specified date range
    current_date = check_from_date
    while current_date < check_until_date:
        # Check if the task was completed on the current date
        task_completed = CleaningSchedule.query.filter_by(
            room_id=room_id,
            action_id=action_id,
            scheduled_date=current_date,
            status='completed'
        ).first()

        # If the task was found to be completed, return True
        if task_completed:
            return True

        # Move to the next day and continue checking
        current_date += timedelta(days=1)

    # Return False if the task was not completed on any day in the specified range
    return False


def get_last_checkout_date_before(room_id, given_date):
    """
    Retrieves the date of the last checkout for a room that occurred before a given date.

    This function finds the most recent checkout date for a specified room that is earlier than
    the provided date. If no checkout is found before the given date, it defaults to a date 7 days prior.

    Parameters:
    room_id (int): The identifier of the room.
    given_date (datetime.date): The date before which to find the last checkout.

    Returns:
    datetime.date: The date of the last checkout before the given date, or a date 7 days prior
    if no checkout date is found.
    """

    # Ensure given_date is in the correct format (date object)
    if isinstance(given_date, datetime):
        given_date = given_date.date()

    # Check if given_date is None and raise an error if it is
    if given_date is None:
        raise ValueError("The given date is None. A valid date is required.")

    # Query to find the last reservation for the room that ended before the given date
    last_reservation = Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.end_date < given_date
    ).order_by(Reservation.end_date.desc()).first()

    # Return the last checkout date if a reservation is found, else return a date 7 days before the given date (
    # Should not happen in practice, except for the first reservation of a room)
    return last_reservation.end_date if last_reservation and last_reservation.end_date else given_date - timedelta(
        days=7)


@cleaning_management_blueprint.route('/toggle_task_status/<int:schedule_id>', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Cleaning')
def change_task_status(schedule_id):
    """
    Flask route to update the status of a specific cleaning task. (Pending/Completed)

    This route handles a POST request to change the status of a cleaning task in the CleaningSchedule database.
    It also updates the performed_timestamp of the task based on the new status.

    Parameters:
    id (int): The identifier of the cleaning task to be updated.

    Returns:
    Flask Response: A JSON response indicating the success or failure of the operation.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    # Extract data from the request's JSON payload
    data = request.get_json()
    task_status = data.get('task_status')  # New status to be set for the task
    completed_date_str = data.get('completed_date')  # The date when the task was completed

    # Validate the presence of required data
    if not completed_date_str:
        return jsonify({"error": "Completed date is required"}), 400

    try:
        # Fetch the task from the database using the provided ID
        task = CleaningSchedule.query.get(schedule_id)
        if not task:
            # Task not found in the database
            return jsonify({"error": "Cleaning task not found"}), 404

        # Update the task status
        task.status = task_status

        # Update the timestamp of when the task was performed based on the task status
        # If the task is completed, set the performed_timestamp to the current UTC time
        task.performed_timestamp = datetime.utcnow() if task_status == 'completed' else None

        # Commit the changes to the database
        db.session.commit()
        log_cleaning_action_performed(user.id, schedule_id, task_status)
        # Return a success message
        return jsonify({"message": "Task marked as completed and future tasks rescheduled"}), 200

    except ValueError:
        # Handle invalid date format error
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD HH:MM"}), 400
    except Exception as e:
        # Rollback in case of any other exceptions and log the error
        db.session.rollback()
        print(e)  # Logging the exception for debugging purposes
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


@cleaning_management_blueprint.route('/get_cleaning_action/<int:action_id>', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_cleaning_action(action_id):
    action = CleaningAction.query.get(action_id)
    if action:
        return jsonify(action.to_dict()), 200
    return jsonify({"msg": "Cleaning action not found"}), 404


@cleaning_management_blueprint.route('/get_cleaning_actions', methods=['GET'])
@jwt_required()
@requires_roles('Admin', 'Manager', 'Reception', 'Cleaning')
def get_cleaning_actions():
    """
    Flask route to retrieve all cleaning action types.

    This route processes a GET request to fetch all entries in the CleaningAction database,
    which represent different types of cleaning actions/tasks that can be scheduled.
    It's useful for understanding the variety of cleaning tasks available and their details.

    Returns:
    Flask Response: A JSON list of all cleaning action types, each converted to a dictionary,
    or an error message in case of an exception.
    """

    try:
        # Debug logging statement - useful for monitoring the function's execution
        print("get cleaning actions")

        # Query the database to retrieve all cleaning action entries in ascending order by ID
        actions = CleaningAction.query.order_by(CleaningAction.id).all()

        # Debug logging statement - indicates successful retrieval of data
        print("got cleaning actions")

        # Convert each cleaning action to a dictionary and return them as a JSON list
        return jsonify([action.to_dict() for action in actions]), 200

    except Exception as e:
        # In case of an exception, log the error and return an error message
        print("Exception occurred:", e)
        return jsonify({'error': str(e)}), 500


@cleaning_management_blueprint.route('/create_cleaning_action', methods=['POST'])
@jwt_required()
@requires_roles('Admin', 'Manager')
def create_cleaning_action():
    """
    Creates a new cleaning action.

    This route processes POST requests to add a new cleaning action to the database.
    It requires JSON data containing 'action_name' and 'frequency_days'.

    Returns:
        JSON response with the created action data and a 201 status code on success.
        JSON response with an error message and a 400 status code if data is missing.
        JSON response with an error message and a 500 status code on server error.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    data = request.get_json()
    action_name = data.get('action_name')
    frequency_days = data.get('frequency_days')

    if not action_name or frequency_days is None:
        return jsonify({"msg": "Missing action name or frequency"}), 400

    new_action = CleaningAction(action_name=action_name, frequency_days=frequency_days)

    try:
        db.session.add(new_action)
        db.session.commit()
        log_cleaning_action_modified(user.id, new_action.id, "Create new cleaning action")
        return jsonify(new_action.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@cleaning_management_blueprint.route('/remove_cleaning_action/<int:action_id>', methods=['DELETE'])
@jwt_required()
@requires_roles('Admin', 'Manager')
def remove_cleaning_action(action_id):
    """
    Deletes a cleaning action and its related scheduled tasks.

    This route processes DELETE requests to remove a specific cleaning action
    identified by 'action_id'. It also deletes any associated scheduled tasks.

    Returns:
        JSON response with a success message and a 200 status code on successful deletion.
        JSON response with an error message and a 404 status code if the action is not found.
        JSON response with an error message and a 500 status code on server error.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    action = CleaningAction.query.get(action_id)
    if action:
        try:
            CleaningSchedule.query.filter_by(action_id=action_id).delete()
            db.session.delete(action)
            db.session.commit()
            log_cleaning_action_modified(user.id, action.id, "Delete cleaning action")
            return jsonify({"msg": "Action removed"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Action not found"}), 404


@cleaning_management_blueprint.route('/modify_cleaning_action/<int:action_id>', methods=['PUT'])
@jwt_required()
@requires_roles('Admin', 'Manager')
def modify_cleaning_action(action_id):
    """
    Modifies an existing cleaning action.

    This route processes PUT requests to update the details of a cleaning action
    identified by 'action_id'. It expects JSON data with updated 'action_name'
    and/or 'frequency_days'.

    Returns:
        JSON response with the updated action data and a 200 status code on success.
        JSON response with an error message and a 404 status code if the action is not found.
        JSON response with an error message and a 500 status code on server error.
    """
    current_user_email = get_jwt_identity()  # Get the user's email from the token
    user = User.query.filter_by(email=current_user_email).first()

    action = CleaningAction.query.get(action_id)
    if action:
        data = request.get_json()
        action_name = data.get('action_name')
        frequency_days = data.get('frequency_days')

        if action_name is not None:
            action.action_name = action_name
        if frequency_days is not None:
            action.frequency_days = frequency_days

        try:
            db.session.commit()
            log_cleaning_action_modified(user.id, action.id, "Modify cleaning action")
            return jsonify(action.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"msg": "Action not found"}), 404


def log_cleaning_action_performed(user_id, schedule_id, action_status):
    """
    Log cleaning action performed.

    Args:
        user_id (int): The ID of the user involved in the action.
        action_id (int): The ID of the cleaning action performed.

    Logs the details of the action along with user information.

    Example of logged details:
    "Action: Linens | Room: 103
    :param action_status: Pending/Completed
    :param user_id: The ID of the user involved in the action.
    :param schedule_id: The ID of the cleaning action performed.
    """
    schedule = CleaningSchedule.query.get(schedule_id)
    action = CleaningAction.query.get(schedule.action_id)
    log_action = "Cleaning Action Status: " + action_status
    room = Room.query.get(schedule.room_id)
    details = f"Action: {action.action_name} | Room: {room.room_name}"
    logs.log_action(user_id, log_action, details)


def log_cleaning_for_day_scheduled(date):
    """
    Log cleaning action scheduled for a day.

    Args:
        date (date): The date of the scheduled cleaning action.

    Logs the details of the action along with the date it's scheduled for.

    Example of logged details:
    "Date: 2020-11-01
    :param date: The date of the cleanings scheduled.
    """
    log_action = "Auto Scheduled Cleaning for Day"
    details = f"Date: {date}"
    logs.log_action(0, log_action, details)


def log_cleaning_action_modified(user_id, action_id, action):
    """
    Log cleaning action modified.

    Args:
        user_id (int): The ID of the user involved in the action.
        action_id (int): The ID of the cleaning action performed.

    Logs the details of the action along with user information.

    Example of logged details:
    "Action: Linens | Room: 103
    :param action: Type of modification
    :param user_id: The ID of the user involved in the action.
    :param action_id: The ID of the cleaning action performed.
    """
    cleaning_action = CleaningAction.query.get(action_id)
    details = f"Action: {action_id} : {cleaning_action.action_name} | Frequency: {cleaning_action.frequency_days}"
    logs.log_action(user_id, action, details)
