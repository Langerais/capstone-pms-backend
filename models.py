from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

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
