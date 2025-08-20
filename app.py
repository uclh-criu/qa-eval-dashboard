from flask import Flask
from flask_login import LoginManager
from models import db, User
import os
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///medical_qa_feedback.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with app
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import and register routes
from routes import register_routes
register_routes(app)

if __name__ == '__main__':
    # Removed db.create_all() as migrations will handle database creation and updates
    # with app.app_context():
    #    db.create_all()
    #    print("Database tables created successfully!")
    
    app.run(debug=True)