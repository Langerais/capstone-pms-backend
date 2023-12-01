from flask_sqlalchemy import SQLAlchemy

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
