import datetime as datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Room(db.Model):
    __tablename__ = 'rooms'  # Explicitly specify the table name

    id = db.Column(db.Integer, primary_key=True)
    channel_manager_id = db.Column(db.String(255), unique=True)
    room_name = db.Column(db.String(255))
    max_guests = db.Column(db.Integer, default=2)
    number_of_beds = db.Column(db.Integer)

    def to_dict(self):
        return {
            'id': self.id,
            'channel_manager_id': self.channel_manager_id,
            'room_name': self.room_name,
            'max_guests': self.max_guests,
            'number_of_beds': self.number_of_beds
        }


class RoomCleaningStatus(db.Model):  # TODO: Remove this model
    __tablename__ = 'room_cleaning_status'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    status = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class Guest(db.Model):
    __tablename__ = 'guests'
    id = db.Column(db.Integer, primary_key=True)
    channel_manager_id = db.Column(db.String(255), unique=True, default=None)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    def to_dict(self):
        return {
            'id': self.id,
            'channel_manager_id': self.channel_manager_id,
            'name': self.name,
            'surname': self.surname,
            'phone': self.phone,
            'email': self.email
        }


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    channel_manager_id = db.Column(db.String(255), unique=True, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'))
    due_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.Enum('Pending', 'Checked-in', 'Checked-out', name='reservation_status'), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        default=6)  # 6-Admin (Temporary) TODO: Remove default value

    def to_dict(self):
        return {
            'id': self.id,
            'channel_manager_id': self.channel_manager_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'room_id': self.room_id,
            'guest_id': self.guest_id,
            'due_amount': str(self.due_amount),
            'status': self.status if self.status else None,
            'user_id': str(self.user_id)
        }


class ReservationStatusChange(db.Model):
    __tablename__ = 'reservation_status_changes'
    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'))
    status = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id
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


class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    category = db.relationship('MenuCategory', backref=db.backref('items', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'description': self.description,
            'price': str(self.price)  # Convert Decimal to string for JSON serialization
        }


class Balance(db.Model):
    __tablename__ = 'balance'

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False,
                             default=0)  # 0 for cash payments, -1 for credit card payments
    transaction_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    number_of_items = db.Column(db.Integer, nullable=False, default=1)

    reservation = db.relationship('Reservation', backref=db.backref('balances', lazy=True))
    menu_item = db.relationship('MenuItem', backref=db.backref('balances', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'reservation_id': self.reservation_id,
            'menu_item_id': self.menu_item_id,
            'transaction_timestamp': self.transaction_timestamp.isoformat(),
            'amount': str(self.amount),
            'number_of_items': self.number_of_items  # Include in to_dict method
        }


class CleaningAction(db.Model):
    __tablename__ = 'cleaning_actions'

    id = db.Column(db.Integer, primary_key=True)
    action_name = db.Column(db.String(255), nullable=False)
    frequency_days = db.Column(db.Integer, nullable=False)  # The frequency of the action in days

    def to_dict(self):
        return {
            'id': self.id,
            'action_name': self.action_name,
            'frequency_days': self.frequency_days
        }


class CleaningSchedule(db.Model):
    __tablename__ = 'cleaning_schedule'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    action_id = db.Column(db.Integer, db.ForeignKey('cleaning_actions.id'), nullable=False)
    performed_timestamp = db.Column(db.Date, nullable=True, default=None)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # e.g., 'pending', 'completed'

    room = db.relationship('Room', backref=db.backref('cleaning_schedules', lazy=True))
    action = db.relationship('CleaningAction', backref=db.backref('cleaning_schedules', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'action_id': self.action_id,
            'performed_timestamp': self.performed_timestamp.isoformat() if self.performed_timestamp else None,
            'scheduled_date': self.scheduled_date.isoformat(),
            'status': self.status
        }


class AppNotification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    department = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    expiry_date = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'department': self.department,
            'priority': self.priority,
            'expiry_date': self.expiry_date.isoformat()
        }
