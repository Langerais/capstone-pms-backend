from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from getSecret import get_secret
from sqlalchemy import text


app = Flask(__name__)

secret = get_secret()
db_username = secret['username']
db_password = secret['password']
#db_name = secret['dbInstanceIdentifier']
db_name = 'postgres'
db_host = secret['host']
db_port = secret['port']

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}'


db = SQLAlchemy(app)

@app.route('/')
def test_db():
    try:
        with db.session.begin():
            # Wrap the SQL query with text()
            db.session.execute(text('SELECT 1'))
            return 'Database connection successful.'
    except Exception as e:
        return f'An error occurred: {e}'



if __name__ == '__main__':
    #print(test_db())
    app.run(host='0.0.0.0', debug=True)


