"""
AuraCrypt Admin Dashboard Logic
"""

from app.models import User, Message, AuditLog, SystemMetric, File
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

class AdminManager:
    """Manages system statistics and administrative actions"""
    
    @staticmethod
    def get_system_stats():
        """Get high-level system statistics"""
        return {
            'total_users': User.query.count(),
            'total_messages': Message.query.count(),
            'total_files': File.query.count(),
            'total_logs': AuditLog.query.count(),
            'active_users_24h': User.query.filter(User.last_login >= datetime.utcnow() - timedelta(days=1)).count(),
            'failed_logins_24h': AuditLog.query.filter(
                AuditLog.action == 'login_failed',
                AuditLog.created_at >= datetime.utcnow() - timedelta(days=1)
            ).count()
        }

    @staticmethod
    def get_user_management_data():
        """Get data for user management dashboard"""
        return User.query.all()

    @staticmethod
    def search_audit_logs(query=None, action_type=None, user_id=None):
        """Advanced audit log search"""
        logs = AuditLog.query
        
        if query:
            logs = logs.filter(AuditLog.details.contains(query) | AuditLog.action.contains(query))
        if action_type:
            logs = logs.filter_by(action_type=action_type)
        if user_id:
            logs = logs.filter_by(user_id=user_id)
            
        return logs.order_by(AuditLog.created_at.desc()).limit(100).all()

    @staticmethod
    def track_performance(metric_name, value, details=None):
        """Store performance metrics"""
        metric = SystemMetric(
            metric_type='performance',
            metric_name=metric_name,
            value=value,
            details=details
        )
        db.session.add(metric)
        db.session.commit()
