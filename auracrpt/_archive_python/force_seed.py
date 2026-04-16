from app import create_app
from app.extensions import db
from app.models import User
from app.auth import AuthenticationManager

app = create_app('development')
with app.app_context():
    db.create_all()
    
    test_users = [
        ('alice', 'alice@example.com', 'password123', 'sender'),
        ('bob', 'bob@example.com', 'password123', 'receiver'),
        ('charlie', 'charlie@example.com', 'password123', 'user'),
        ('admin', 'admin@example.com', 'admin123', 'admin'),
    ]
    
    for username, email, password, role in test_users:
        if not User.query.filter_by(username=username).first():
            user, error = AuthenticationManager.register_user(username, email, password, role)
            if user:
                print(f'Created user: {username} ({role})')
            else:
                print(f'Failed to create user {username}: {error}')
    
    print('Database seeding complete!')
