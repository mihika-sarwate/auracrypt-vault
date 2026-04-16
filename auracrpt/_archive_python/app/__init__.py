"""
AuraCrypt Flask Application Factory
"""

import os
import sys
from flask import Flask
from flask_login import LoginManager

def create_app(config_name=None):
    """Create and configure Flask application"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Import config after Flask app creation
    from config import config
    app.config.from_object(config.get(config_name, config['development']))
    
    # Import and initialize extensions
    from app.extensions import db, socketio
    from app.models import User
    db.init_app(app)
    socketio.init_app(app)
    
    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page'
    
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register IDS middleware
    from app.ids_middleware import register_ids_middleware
    register_ids_middleware(app)
    
    # Register blueprints
    from app.routes import auth_bp, main_bp, api_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Page not found'}, 404
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Access forbidden'}, 403
    
    @app.errorhandler(500)
    def server_error(error):
        return {'error': 'Internal server error'}, 500
    
    return app
