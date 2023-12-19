# Description: The main file of the application. Contains the Flask app and the database engine.
from flask import Flask, jsonify, request, current_app
from flask_apscheduler import APScheduler
from sqlalchemy.orm import sessionmaker
from getSecret import get_secret
from sqlalchemy import text, create_engine
from datetime import datetime, timedelta
from logs import logging_blueprint
from models import db, AppNotification, Reservation, Guest, Room, CleaningSchedule
from auth import auth_blueprint
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from getEntities import get_entities_blueprint
from registration import registration_blueprint
from guest_management import guest_management_blueprint
from reservations_management import reservations_management_blueprint, calculate_unpaid_amount_internal
from room_management import room_management_blueprint
from user_management import user_management_blueprint
from menu_management import menu_management_blueprint
from cleaning_management import cleaning_management_blueprint, schedule_cleaning_internal
from config import SCHEDULER_INTERVAL_CRON_10MIN, SCHEDULER_INTERVAL_1MIN

# TODO: User role checks all over the place

app = Flask(__name__)

# Initialize APScheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Import the notifications_management module
from notifications_management import notifications_management_blueprint, create_notification_logic

jwt = JWTManager(app)
bcrypt = Bcrypt(app)

# Get the secret from AWS Secret Manager
secret = get_secret()

# Set the database URI
db_username = secret['username']
db_password = secret['password']
# db_name = secret['dbInstanceIdentifier']
db_name = 'postgres'
db_host = secret['host']
db_port = secret['port']
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'

# Create a database engine
db_engine = create_engine(f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}')

# Create a session factory with timezone set to 'Europe/Athens'
Session = sessionmaker(bind=db_engine, expire_on_commit=False, timezone='Europe/Athens')

db.init_app(app)  # Initialize db with the app context

# Register the blueprints
app.register_blueprint(get_entities_blueprint, url_prefix='/api')  # TODO: Remove this
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(registration_blueprint, url_prefix='/auth')
app.register_blueprint(guest_management_blueprint, url_prefix='/guests')
app.register_blueprint(reservations_management_blueprint, url_prefix='/reservations')
app.register_blueprint(room_management_blueprint, url_prefix='/rooms')
app.register_blueprint(user_management_blueprint, url_prefix='/users')
app.register_blueprint(menu_management_blueprint, url_prefix='/menu')
app.register_blueprint(cleaning_management_blueprint, url_prefix='/cleaning_management')
app.register_blueprint(logging_blueprint, url_prefix='/logging')
app.register_blueprint(notifications_management_blueprint, url_prefix='/notifications')


@app.route('/')
def test_db():  # TODO: Remove this
    try:
        with db.session.begin():
            # Wrap the SQL query with text()
            db.session.execute(text('SELECT 1'))
            return 'Database connection successful.\n'
    except Exception as e:
        return f'An error occurred: {e}'


@app.route('/get_timezone')
def get_timezone():
    return jsonify({'timezone': 'Europe/Athens'})


if __name__ == '__main__':
    app.run()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)  # TODO: Fix ssl_context (HTTPS doesn't work)


def delete_expired_notifications():  # Tested-
    print("Deleting expired notifications")

    # Use the Flask application context
    with app.app_context():
        # Print time of execution

        print(datetime.now())
        expired_notifications = AppNotification.query.filter(AppNotification.expiry_date < datetime.now()).all()

        for notification in expired_notifications:
            db.session.delete(notification)
        db.session.commit()

    print("Expired notifications deletion completed")


def check_departures_create_notifications():  # Tested
    print("Checking reservations")
    with app.app_context():
        reservations = Reservation.query.filter(
            Reservation.end_date >= datetime.now(),
            Reservation.end_date <= datetime.now() + timedelta(hours=24)
        ).all()

        for reservation in reservations:
            if not reservation.status == 'Checked-out':
                unpaid_amount = calculate_unpaid_amount_internal(reservation.id)
                if unpaid_amount <= 0:
                    room = Room.query.filter(Room.id == reservation.room_id).first()
                    guest = Guest.query.filter(Guest.id == reservation.guest_id).first()
                    title = f"Expected Departure: {room.room_name}"
                    message = f"{guest.name} {guest.surname}"
                    expiry_date = datetime.now() + timedelta(minutes=29, seconds=59)
                    for department in ['Admin', 'Managers', 'Receptionists', 'Cleaning']:
                        create_notification_logic(
                            title=title,
                            message=message,
                            department=department,
                            priority=3,
                            manager_id=0,  # SYSTEM User
                            expiry_date=expiry_date,
                        )
                else:
                    room = Room.query.filter(Room.id == reservation.room_id).first()
                    guest = Guest.query.filter(Guest.id == reservation.guest_id).first()
                    title = f"UNPAID DEPARTURE: {room.room_name}"
                    message = f"{guest.name} {guest.surname} | Due: {unpaid_amount}€"
                    expiry_date = datetime.now() + timedelta(minutes=29, seconds=59)
                    for department in ['Admin', 'Managers', 'Receptionists', 'Bar/Restoraunt']:
                        create_notification_logic(
                            title=title,
                            message=message,
                            department=department,
                            priority=-1,
                            manager_id=0,  # SYSTEM User
                            expiry_date=expiry_date,
                        )
    print("Checking reservations completed")


def check_arrivals_create_notifications():
    print("Checking for upcoming arrivals")
    with app.app_context():
        reservations = Reservation.query.filter(
            Reservation.start_date >= datetime.now(),
            Reservation.start_date <= datetime.now() + timedelta(hours=24)
        ).all()

        for reservation in reservations:
            room = Room.query.filter(Room.id == reservation.room_id).first()
            guest = Guest.query.filter(Guest.id == reservation.guest_id).first()

            # Check for cleaning schedule
            cleaning_schedule = CleaningSchedule.query.filter(
                CleaningSchedule.room_id == room.id,
                CleaningSchedule.scheduled_date == datetime.now().date(),
                CleaningSchedule.status == 'pending'
            ).all()

            # Create arrival notifications
            title = f"ARRIVAL: {room.room_name}"
            message = f"Expected Arrival: {guest.name} {guest.surname}"
            expiry_date = datetime.now() + timedelta(minutes=29, seconds=59)
            for department in ['Admin', 'Managers', 'Receptionists']:
                create_notification_logic(
                    title=title,
                    message=message,
                    department=department,
                    priority=2,
                    manager_id=0,
                    expiry_date=expiry_date,
                )

            # Create cleaning reminder notifications if there are pending cleaning tasks
            if cleaning_schedule:
                pending_actions = ', '.join([action.action.action_name for action in cleaning_schedule])
                clean_title = f"REQUIRED PRE-ARRIVAL CLEANING: {room.room_name}"
                clean_message = f"Pending Actions: {pending_actions}"
                clean_expiry_date = datetime.now() + timedelta(minutes=29, seconds=59)
                for department in ['Admin', 'Managers', 'Cleaning']:
                    create_notification_logic(
                        title=clean_title,
                        message=clean_message,
                        department=department,
                        priority=1,
                        manager_id=0,
                        expiry_date=clean_expiry_date,
                    )

    print("Arrival checks completed")


# Schedule cleaning for today, every 24h
def schedule_cleaning_for_today():
    with app.app_context():
        schedule_cleaning_internal()


# Schedule the jobs

# Delete expired notifications every minute
scheduler.add_job(
    id='delete_expired',
    func=delete_expired_notifications,
    trigger='cron',
    second='0'
)

# Check for upcoming arrivals for the next 24 hours every 30 minutes (Notifications lifetime is 30 minutes)
scheduler.add_job(
    id='check_departures',
    func=check_departures_create_notifications,
    trigger='cron',
    minute='0, 30'
)

# Check for upcoming arrivals for the next 24 hours every 30 minutes (Notifications lifetime is 30 minutes)
scheduler.add_job(
    id='check_arrivals',
    func=check_arrivals_create_notifications,
    trigger='cron',
    minute='0, 30'
)

# Schedule cleaning for today, every 24h at 3:00 AM
scheduler.add_job(
    id='schedule_cleaning',
    func=schedule_cleaning_for_today,
    trigger='cron',
    hour='3',
    minute='0',
)

scheduler.start()
