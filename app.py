from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Replace the below database URI with your actual database credentials
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def test_db():
    try:
        db.engine.execute('SELECT 1')  # Simple query to test the database connection
        return 'Database connection successful.'
    except Exception as e:
        return f'An error occurred: {e}'

if __name__ == '__main__':
    app.run(debug=True)

