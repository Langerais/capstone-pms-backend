from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from getSecret import get_secret
from sqlalchemy import text
from models import db
from auth import auth_blueprint
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from getEntities import get_entities_blueprint
from registration import registration_blueprint
from guest_management import guest_management_blueprint
from reservations_management import reservations_management_blueprint
from room_management import room_management_blueprint
from user_management import user_management_blueprint

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = '1234567890'  # TODO: Change to value from secret manager
jwt = JWTManager(app)
bcrypt = Bcrypt(app)

secret = get_secret()
db_username = secret['username']
db_password = secret['password']
# db_name = secret['dbInstanceIdentifier']
db_name = 'postgres'
db_host = secret['host']
db_port = secret['port']

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'

# db = SQLAlchemy(app) # TODO: Remove this line

db.init_app(app)  # Initialize db with the app context

# Register the blueprints
app.register_blueprint(get_entities_blueprint, url_prefix='/api')
app.register_blueprint(auth_blueprint, url_prefix='/auth')
app.register_blueprint(registration_blueprint, url_prefix='/auth')
app.register_blueprint(guest_management_blueprint, url_prefix='/guests')
app.register_blueprint(reservations_management_blueprint, url_prefix='/reservations')
app.register_blueprint(room_management_blueprint, url_prefix='/rooms')
app.register_blueprint(user_management_blueprint, url_prefix='/users')


@app.route('/test/admin', methods=['GET'])
@jwt_required()
def test_admin_access():
    claims = get_jwt()
    department = claims.get('department')

    if department == 'Admin':
        return jsonify({"msg": "Access granted, you are an Admin"}), 200

    return jsonify({"msg": "Access denied, you are not an Admin"}), 403


@app.route('/')
def test_db():
    try:
        with db.session.begin():
            # Wrap the SQL query with text()
            db.session.execute(text('SELECT 1'))
            return 'Database connection successful.\n'
    except Exception as e:
        return f'An error occurred: {e}'


if __name__ == '__main__':
    # print(test_db())
    app.run(host='0.0.0.0', debug=True, port=5000)  # TODO: Fix ssl_context (HTTPS doesn't work)
