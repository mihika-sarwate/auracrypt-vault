"""
AuraCrypt Authentication Module
Handles user registration, login, and role-based access control
"""

from flask import current_app
from functools import wraps
from flask_login import current_user
from flask import abort
from app.models import User, PublicKey, AuditLog
from app.extensions import db
from app.cryptography import RSAKeyManager
from datetime import datetime, timedelta
import pyotp
import qrcode
import io
import base64


class AuthenticationManager:
    """Manages user authentication and authorization"""
    
    @staticmethod
    def register_user(username, email, password, role='user'):
        """
        Register a new user
        Args:
            username: unique username
            email: user email
            password: plaintext password (will be hashed)
            role: user role ('user', 'sender', 'receiver')
        Returns: User object or error message
        """
        # Validate inputs
        if not username or not email or not password:
            return None, "All fields are required"
        
        if len(password) < 8:
            return None, "Password must be at least 8 characters"
        
        if '@' not in email:
            return None, "Invalid email address"
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        
        if User.query.filter_by(email=email).first():
            return None, "Email already registered"
        
        try:
            # Create user
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            
            # Generate RSA keypair for user
            key_manager = RSAKeyManager(key_size=2048)
            private_key, public_key = key_manager.generate_keypair()
            
            # Store public key
            public_key_record = PublicKey(
                user_id=user.id,
                public_key=key_manager.serialize_public_key(public_key),
                key_size=2048
            )
            db.session.add(public_key_record)
            db.session.commit()
            
            # Log registration
            AuditLog.log_action(
                user_id=user.id,
                action='user_registered',
                action_type='registration',
                status='success'
            )
            
            return user, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"Registration failed: {str(e)}"
    
    @staticmethod
    def authenticate_user(identifier, password):
        """
        Authenticate user with username and password
        Args:
            username: username
            password: plaintext password
        Returns: User object or None
        """
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
        
        if user and user.check_password(password) and user.is_active:
            user.update_last_login()
            return user
        
        return None
    
    @staticmethod
    def get_user_public_key(user_id):
        """
        Retrieve user's public key
        Args:
            user_id: user ID
        Returns: PublicKey object or None
        """
        return PublicKey.query.filter_by(user_id=user_id, is_active=True).first()
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def rotate_user_keys(user_id):
        """
        Generate new RSA keypair for user
        Args:
            user_id: user ID
        Returns: new public key or None
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Deactivate old key
            old_key = PublicKey.query.filter_by(user_id=user_id, is_active=True).first()
            if old_key:
                old_key.is_active = False
            
            # Generate new keypair
            key_manager = RSAKeyManager(key_size=2048)
            private_key, public_key = key_manager.generate_keypair()
            
            # Store new public key
            new_key = PublicKey(
                user_id=user_id,
                public_key=key_manager.serialize_public_key(public_key),
                key_size=2048
            )
            db.session.add(new_key)
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='keys_rotated',
                action_type='key_rotation',
                status='success'
            )
            
            return new_key
        
        except Exception as e:
            db.session.rollback()
            return None
    @staticmethod
    def setup_2fa(user_id):
        """Generate a 2FA secret and provisioning URL for a user"""
        user = User.query.get(user_id)
        if not user:
            return None, "User not found"
        
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        db.session.commit()
        
        provisioning_url = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email,
            issuer_name="AuraCrypt"
        )
        
        # Generate QR code as base64
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_base64}"
        }, None

    @staticmethod
    def verify_2fa(user_id, token):
        """Verify a 2FA token"""
        user = User.query.get(user_id)
        if not user or not user.two_factor_secret:
            return False
        
        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(token)

    @staticmethod
    def enable_2fa(user_id, token):
        """Verify and enable 2FA for a user"""
        if AuthenticationManager.verify_2fa(user_id, token):
            user = User.query.get(user_id)
            user.is_2fa_enabled = True
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='2fa_enabled',
                action_type='security',
                status='success'
            )
            return True, None
        return False, "Invalid 2FA token"

    @staticmethod
    def disable_2fa(user_id):
        """Disable 2FA for a user"""
        user = User.query.get(user_id)
        if user:
            user.is_2fa_enabled = False
            user.two_factor_secret = None
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='2fa_disabled',
                action_type='security',
                status='success'
            )
            return True
        return False


class RoleBasedAccessControl:
    """Implements role-based access control"""
    
    ROLES = {
        'user': ['view_dashboard', 'manage_profile'],
        'sender': ['view_dashboard', 'manage_profile', 'embed_message'],
        'receiver': ['view_dashboard', 'manage_profile', 'extract_message'],
    }
    
    @staticmethod
    def require_role(*roles):
        """Decorator to restrict access to specific roles"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    abort(401)
                
                if current_user.role not in roles:
                    abort(403)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def require_permission(permission):
        """Decorator to restrict access to users with specific permission"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not current_user.is_authenticated:
                    abort(401)
                
                allowed_permissions = RoleBasedAccessControl.ROLES.get(current_user.role, [])
                if permission not in allowed_permissions:
                    abort(403)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def user_has_permission(user, permission):
        """Check if user has specific permission"""
        if not user:
            return False
        
        allowed_permissions = RoleBasedAccessControl.ROLES.get(user.role, [])
        return permission in allowed_permissions
    
    @staticmethod
    def user_has_role(user, role):
        """Check if user has specific role"""
        return user and user.role == role


# Extend AuditLog model with logging method
@staticmethod
def log_action(user_id=None, action='', action_type='', status='success', ip_address=None, details=None, error_message=None):
    """Log an action for audit trail"""
    try:
        from flask import request
        
        log = AuditLog(
            user_id=user_id,
            action=action,
            action_type=action_type,
            status=status,
            ip_address=ip_address or request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:512],
            details=details,
            error_message=error_message
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        # Don't crash on audit log errors
        pass

AuditLog.log_action = log_action
