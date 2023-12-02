from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

db = SQLAlchemy()

# TODO: Add models: Restaurant/Bar order, Menu entry, Notification (?), Payment, Cleaning action (?);


class Room(db.Model):
    __tablename__ = 'rooms'  # Explicitly specify the table name

    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(255))
    max_guests = db.Column(db.Integer)
    number_of_beds = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id,
            'room_name': self.room_name,
            'max_guests': self.max_guests,
            'number_of_beds': self.number_of_beds
        }


class RoomCleaningStatus(db.Model):
    __tablename__ = 'room_cleaning_status'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    status = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class Guest(db.Model):
    __tablename__ = 'guests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'phone': self.phone,
            'email': self.email
        }


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    channel_manager_id = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'))
    due_amount = db.Column(db.Numeric(10, 2))

    def to_dict(self):
        return {
            'id': self.id,
            'channel_manager_id': self.channel_manager_id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'room_id': self.room_id,
            'guest_id': self.guest_id,
            'due_amount': str(self.due_amount)
        }


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'surname': self.surname,
            'phone': self.phone,
            'email': self.email,
            'department': self.department
        }


# Department model, also used as user role
class Department(db.Model):
    __tablename__ = 'departments'
    department_name = db.Column(db.String(100), primary_key=True)
    description = db.Column(db.Text)

    def to_dict(self):
        return {
            'department_name': self.department_name,
            'description': self.description
        }
