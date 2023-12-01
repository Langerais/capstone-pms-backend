from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from getSecret import get_secret
from sqlalchemy import text
from models import db
from getEntities import get_entities_blueprint


app = Flask(__name__)

secret = get_secret()
db_username = secret['username']
db_password = secret['password']
#db_name = secret['dbInstanceIdentifier']
db_name = 'postgres'
db_host = secret['host']
db_port = secret['port']

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'


#db = SQLAlchemy(app) # TODO: Remove this line

db.init_app(app)  # Initialize db with the app context

app.register_blueprint(get_entities_blueprint, url_prefix='/api')  # Register the blueprint

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
    #print(test_db())
    app.run(host='0.0.0.0', debug=True, port=5000) #TODO: Fix ssl_context (HTTPS doesn't work)


