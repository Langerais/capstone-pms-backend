from datetime import datetime

import requests
from lxml import etree

from models import Reservation, db


def update_reservations_from_ota():
    try:
        xml_data = fetch_ota_data()
        reservations_data = parse_ota_data(xml_data)
        save_reservations(reservations_data)
    except Exception as e:
        print(f"Error updating reservations: {e}")


def fetch_and_parse_ota_data():
    response = requests.get('YOUR_API_ENDPOINT')
    if response.status_code == 200:
        xml_data = etree.fromstring(response.content)
        # Parse data and map to your database schema
        return xml_data
    else:
        raise Exception('Failed to fetch OTA data')


def fetch_ota_data():
    response = requests.get('YOUR_OTA_API_ENDPOINT')
    if response.status_code == 200:
        return response.content
    else:
        raise Exception('Failed to fetch OTA data')


def parse_ota_data(xml_data):
    root = etree.fromstring(xml_data)
    reservations = []

    for hotel_res in root.findall('.//HotelReservation'):
        res_data = {
            'channel_manager_id': hotel_res.findtext('.//UniqueID[@Type="14"]/@ID'),
            'create_date_time': hotel_res.get('CreateDateTime'),
            'last_modify_date_time': hotel_res.get('LastModifyDateTime'),
            'res_status': hotel_res.get('ResStatus'),
            'start_date': hotel_res.findtext('.//TimeSpan/@Start'),
            'end_date': hotel_res.findtext('.//TimeSpan/@End'),
            'guest_id': None,  # To be mapped
            'room_id': None,  # To be mapped
            'due_amount': None,  # To be computed
            'status': hotel_res.get('ResStatus')
        }

        guest_id = hotel_res.findtext('.//Profiles/ProfileInfo/Profile/Customer/PersonName/Surname')
        room_id = hotel_res.findtext('.//RoomTypes/RoomType/@RoomTypeCode')

        res_data['guest_id'] = fetch_or_create_guest(guest_id)
        res_data['room_id'] = fetch_or_create_room(room_id)
        res_data['due_amount'] = calculate_due_amount(hotel_res)

        reservations.append(res_data)

    return reservations


def fetch_or_create_guest(guest_id):
    # Implement logic to check if guest exists or create a new guest
    return guest_id

def fetch_or_create_room(room_id):
    # Implement logic to check if room exists or create a new room
    return room_id

def calculate_due_amount(hotel_reservation, due_amount=None):
    # Implement logic to calculate due amount from hotel_reservation data
    return due_amount



def save_reservations(reservations_data):
    for data in reservations_data:
        reservation = Reservation(
            channel_manager_id=data['channel_manager_id'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
            guest_id=data['guest_id'],
            room_id=data['room_id'],
            due_amount=data['due_amount'],
            status=data['status']
        )
        db.session.add(reservation)
    db.session.commit()

