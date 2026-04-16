#!/usr/bin/env python
"""
Database initialization script
Creates database tables and seeds with test data
"""

import os
import sys
from app import create_app, db
from app.models import User, PublicKey
from app.auth import AuthenticationManager

def init_database():
    """Initialize database with tables"""
    app = create_app('development')
    
    with app.app_context():
        # Drop all tables (optional - comment out for production)
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Seed test users
        seed_test_users()
        
        print("\nDatabase initialization complete!")

def seed_test_users():
    """Seed database with test users"""
    test_users = [
        ('alice', 'alice@example.com', 'password123', 'sender'),
        ('bob', 'bob@example.com', 'password123', 'receiver'),
        ('charlie', 'charlie@example.com', 'password123', 'user'),
    ]
    
    print("\nSeeding test users...")
    for username, email, password, role in test_users:
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"  - {username} (already exists)")
            continue
        
        try:
            user, error = AuthenticationManager.register_user(username, email, password, role)
            if user:
                print(f"  ✓ Created {username} ({role})")
            else:
                print(f"  ✗ Failed to create {username}: {error}")
        except Exception as e:
            print(f"  ✗ Error creating {username}: {str(e)}")
    
    print("Seeding complete!")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
