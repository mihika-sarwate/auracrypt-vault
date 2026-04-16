"""
AuraCrypt API Key Management
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from app.models import APIKey, AuditLog
from app.extensions import db

class APIKeyManager:
    """Manages API keys for programmatic access"""
    
    @staticmethod
    def generate_key(user_id, name, expires_in_days=30):
        """Generate a new API key for a user"""
        try:
            # Generate key
            api_key = f"ac_{secrets.token_urlsafe(32)}"
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Set expiry
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            # Save to DB
            new_key = APIKey(
                user_id=user_id,
                key_hash=key_hash,
                name=name,
                expires_at=expires_at
            )
            
            db.session.add(new_key)
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='api_key_generated',
                action_type='api_key',
                status='success',
                details=f'Key Name: {name}'
            )
            
            return api_key, new_key
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def verify_key(api_key):
        """Verify an API key and return the associated user"""
        if not api_key:
            return None
            
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_record = APIKey.query.filter_by(key_hash=key_hash, is_active=True).first()
        
        if not key_record:
            return None
            
        # Check expiry
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            key_record.is_active = False
            db.session.commit()
            return None
            
        # Update last used
        key_record.last_used_at = datetime.utcnow()
        db.session.commit()
        
        return key_record.user

    @staticmethod
    def revoke_key(user_id, key_id):
        """Revoke an API key"""
        try:
            key_record = APIKey.query.filter_by(id=key_id, user_id=user_id).first()
            if not key_record:
                return False, "Key not found"
                
            key_record.is_active = False
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='api_key_revoked',
                action_type='api_key',
                status='success'
            )
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
