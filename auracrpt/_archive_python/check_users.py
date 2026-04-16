from app import create_app
from app.extensions import db
from app.models import User
import os

app = create_app('development')
with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # For relative sqlite paths, let's find the absolute path
    # Flask-SQLAlchemy doesn't directly expose the resolved path always, but we can check the engine
    try:
        from sqlalchemy import inspect
        print(f"Database File: {app.instance_path}")
    except:
        pass
        
    count = User.query.count()
    print(f"User count: {count}")
    users = User.query.all()
    for user in users:
        print(f" - {user.username} ({user.email})")
