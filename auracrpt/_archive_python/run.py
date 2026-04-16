#!/usr/bin/env python
"""
AuraCrypt Application Entry Point
Run this script to start the Flask development server
"""

import os
from app import create_app
from app.extensions import db, socketio
from app.models import User, Message, PublicKey, AuditLog

# Create Flask app
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Application context for CLI commands
@app.shell_context_processor
def make_shell_context():
    """Make models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Message': Message,
        'PublicKey': PublicKey,
        'AuditLog': AuditLog
    }


@app.cli.command()
def init_db():
    """Initialize the database"""
    db.create_all()
    print('Database initialized successfully!')


@app.cli.command()
def seed_db():
    """Seed database with test data"""
    from app.auth import AuthenticationManager
    
    # Create test users
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


if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
