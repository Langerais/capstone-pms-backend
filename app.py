# Description: The main file of the application. Contains the Flask app and the database engine.
from datetime import datetime

from flask import Flask, jsonify, request, current_app
from flask_apscheduler import APScheduler
from sqlalchemy.orm import sessionmaker
from getSecret import get_secret
from sqlalchemy import text, create_engine

from logs import logging_blueprint
from models import db, AppNotification
from auth import auth_blueprint
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from getEntities import get_entities_blueprint
from registration import registration_blueprint
from guest_management import guest_management_blueprint
from reservations_management import reservations_management_blueprint
from room_management import room_management_blueprint
from user_management import user_management_blueprint
from menu_management import menu_management_blueprint
from cleaning_management import cleaning_management_blueprint

# TODO: User role checks all over the place

app = Flask(__name__)

# Initialize APScheduler
scheduler = APScheduler()
scheduler.init_app(app)

# Import the notifications_management module
from notifications_management import notifications_management_blueprint

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
    # print(test_db())
    app.run(host='0.0.0.0', debug=True, port=5000)  # TODO: Fix ssl_context (HTTPS doesn't work)


def delete_expired_notifications():
    print("Deleting expired notifications")

    # Use the Flask application context
    with app.app_context():
        print("Getting expired notifications")
        expired_notifications = AppNotification.query.filter(AppNotification.expiry_date < datetime.now()).all()
        print(f"Found {len(expired_notifications)} expired notifications")

        for notification in expired_notifications:
            db.session.delete(notification)
        db.session.commit()

    print("Expired notifications deletion completed")


# Schedule the jobs

# Delete expired notifications every hour
scheduler.add_job(
    id='delete_expired',
    func=delete_expired_notifications,
    trigger='cron',
    minute='0',
)

scheduler.start()
