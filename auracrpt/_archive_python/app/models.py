"""
AuraCrypt Database Models
Defines database schema for users, files, messages, and audit logs
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

from app.extensions import db


class User(UserMixin, db.Model):
    """User model with role-based access control"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user', 'sender', 'receiver'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    is_2fa_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))

    # Relationships
    public_key_record = db.relationship('PublicKey', backref='owner', uselist=False, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='sender', foreign_keys='Message.sender_id', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', backref='recipient', foreign_keys='Message.recipient_id', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', cascade='all, delete-orphan')
    api_keys = db.relationship('APIKey', backref='user', cascade='all, delete-orphan')
    files = db.relationship('File', backref='owner', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class PublicKey(db.Model):
    """Stores user public keys"""
    __tablename__ = 'public_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)  # PEM format
    key_size = db.Column(db.Integer, default=2048)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<PublicKey for {self.owner.username}>'


class Message(db.Model):
    """Stores messages with embedded data"""
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    recipient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Message metadata
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # File handling
    audio_file_name = db.Column(db.String(255), nullable=False)
    audio_file_path = db.Column(db.String(512), nullable=False)
    audio_file_size = db.Column(db.Integer)  # in bytes
    audio_file_hash = db.Column(db.String(64))  # SHA-256 hash
    
    # Message embedding
    encrypted_message = db.Column(db.Text)  # Encrypted message (hex encoded)
    message_size = db.Column(db.Integer)  # Size of encrypted message in bytes
    embedding_method = db.Column(db.String(50), default='lsb')  # LSB steganography
    
    # Status tracking
    is_extracted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    accessed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Message {self.title} from {self.sender.username}>'


class AuditLog(db.Model):
    """Audit log for security tracking"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    action_type = db.Column(db.String(50))  # 'login', 'embed', 'extract', 'download', 'error'
    status = db.Column(db.String(20), default='success')  # 'success', 'failed'
    
    # Request details
    ip_address = db.Column(db.String(45), index=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(512))
    
    # Additional context
    details = db.Column(db.Text)  # JSON serialized details
    error_message = db.Column(db.Text)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} at {self.created_at}>'


class IPBlockList(db.Model):
    """Stores blocked IP addresses for intrusion detection"""
    __tablename__ = 'ip_blocklist'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = db.Column(db.String(45), unique=True, nullable=False, index=True)
    reason = db.Column(db.String(255))
    blocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_until = db.Column(db.DateTime)  # When block expires
    block_count = db.Column(db.Integer, default=1)  # Number of violations
    
    def __repr__(self):
        return f'<IPBlockList {self.ip_address}>'


class File(db.Model):
    """General file management model"""
    __tablename__ = 'files'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    filesize = db.Column(db.Integer)
    mimetype = db.Column(db.String(100))
    file_hash = db.Column(db.String(64))
    metadata_json = db.Column(db.Text)  # Store extra metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<File {self.filename}>'


class APIKey(db.Model):
    """Stores API keys for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(128), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<APIKey {self.name} for {self.user.username}>'


class SystemMetric(db.Model):
    """Performance and security metrics"""
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_type = db.Column(db.String(50), nullable=False)  # 'performance', 'security', 'usage'
    metric_name = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemMetric {self.metric_name}: {self.value}>'


class RateLimitTracker(db.Model):
    """Tracks request rates per IP for rate limiting"""
    __tablename__ = 'rate_limit_tracker'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    request_count = db.Column(db.Integer, default=0)
    window_start = db.Column(db.DateTime, default=datetime.utcnow)
    last_request = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('ip_address', 'endpoint', name='unique_ip_endpoint'),
    )
    
    def __repr__(self):
        return f'<RateLimitTracker {self.ip_address} @ {self.endpoint}>'
