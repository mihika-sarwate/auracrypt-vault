"""
AuraCrypt Intrusion Detection System Middleware
Implements rate limiting and IP blocking for security
"""

from flask import request
from datetime import datetime, timedelta
from app.models import IPBlockList, RateLimitTracker, AuditLog, db
from functools import wraps as functools_wraps


class IDSMiddleware:
    """Intrusion Detection System Middleware"""
    
    @staticmethod
    def is_ip_blocked(ip_address):
        """Check if IP is currently blocked"""
        blocked = IPBlockList.query.filter_by(ip_address=ip_address).first()
        
        if not blocked:
            return False
        
        # Check if block has expired
        if blocked.blocked_until and blocked.blocked_until < datetime.utcnow():
            # Unblock IP by deleting the record
            db.session.delete(blocked)
            db.session.commit()
            return False
        
        return True
    
    @staticmethod
    def block_ip(ip_address, reason, duration_seconds=3600):
        """Block an IP address"""
        try:
            existing_block = IPBlockList.query.filter_by(ip_address=ip_address).first()
            
            if existing_block:
                existing_block.block_count += 1
                existing_block.blocked_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
                existing_block.reason = reason
            else:
                new_block = IPBlockList(
                    ip_address=ip_address,
                    reason=reason,
                    blocked_until=datetime.utcnow() + timedelta(seconds=duration_seconds),
                    block_count=1
                )
                db.session.add(new_block)
            
            db.session.commit()
            
            AuditLog.log_action(
                action='ip_blocked',
                action_type='security',
                status='success',
                ip_address=ip_address,
                details=f"Reason: {reason}"
            )
            
            return True
        except Exception as e:
            db.session.rollback()
            return False
    
    @staticmethod
    def unblock_ip(ip_address):
        """Unblock an IP address"""
        try:
            blocked = IPBlockList.query.filter_by(ip_address=ip_address).first()
            if blocked:
                db.session.delete(blocked)
                db.session.commit()
                return True
            return False
        except:
            db.session.rollback()
            return False
    
    @staticmethod
    def check_rate_limit(ip_address, endpoint, max_requests=100, window_seconds=3600):
        """
        Check if IP has exceeded rate limit
        Returns: (is_limited, requests_made, requests_remaining)
        """
        now = datetime.utcnow()
        
        try:
            tracker = RateLimitTracker.query.filter_by(
                ip_address=ip_address,
                endpoint=endpoint
            ).first()
            
            if not tracker:
                # Create new tracker
                tracker = RateLimitTracker(
                    ip_address=ip_address,
                    endpoint=endpoint,
                    request_count=1,
                    window_start=now
                )
                db.session.add(tracker)
                db.session.commit()
                return False, 1, max_requests - 1
            
            # Check if window has expired
            window_age = (now - tracker.window_start).total_seconds()
            
            if window_age > window_seconds:
                # Reset window
                tracker.window_start = now
                tracker.request_count = 1
                db.session.commit()
                return False, 1, max_requests - 1
            
            # Increment request count
            tracker.request_count += 1
            tracker.last_request = now
            db.session.commit()
            
            # Check if limit exceeded
            is_limited = tracker.request_count > max_requests
            remaining = max(0, max_requests - tracker.request_count)
            
            return is_limited, tracker.request_count, remaining
        
        except Exception as e:
            # Log error but don't block on middleware error
            return False, 0, max_requests
    
    @staticmethod
    def get_client_ip():
        """Get client IP address, accounting for proxies"""
        if request.environ.get('HTTP_CF_CONNECTING_IP'):
            # Cloudflare
            return request.environ.get('HTTP_CF_CONNECTING_IP')
        elif request.environ.get('HTTP_X_FORWARDED_FOR'):
            # Proxy
            return request.environ.get('HTTP_X_FORWARDED_FOR').split(',')[0]
        else:
            return request.remote_addr


class RateLimitDecorator:
    """Decorator for rate limiting endpoints"""
    
    @staticmethod
    def limit_request_rate(max_requests=100, window_seconds=3600):
        """Decorator to limit request rate per IP"""
        def decorator(f):
            @functools_wraps(f)
            def decorated_function(*args, **kwargs):
                ip_address = IDSMiddleware.get_client_ip()
                
                # Check if IP is blocked
                if IDSMiddleware.is_ip_blocked(ip_address):
                    AuditLog.log_action(
                        action='request_blocked',
                        action_type='security',
                        status='blocked',
                        ip_address=ip_address,
                        details='IP address is blocked'
                    )
                    return {'error': 'Your IP address has been blocked'}, 403
                
                # Check rate limit
                endpoint = request.endpoint or f.__name__
                is_limited, request_count, remaining = IDSMiddleware.check_rate_limit(
                    ip_address,
                    endpoint,
                    max_requests,
                    window_seconds
                )
                
                if is_limited:
                    IDSMiddleware.block_ip(
                        ip_address,
                        f'Rate limit exceeded on {endpoint}',
                        duration_seconds=1800  # Block for 30 minutes
                    )
                    
                    AuditLog.log_action(
                        action='rate_limit_exceeded',
                        action_type='security',
                        status='blocked',
                        ip_address=ip_address,
                        details=f'Exceeded {max_requests} requests in {window_seconds}s'
                    )
                    
                    return {'error': 'Rate limit exceeded'}, 429
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


def register_ids_middleware(app):
    """Register IDS middleware with Flask app"""
    
    @app.before_request
    def check_blocked_ips():
        """Check if incoming request is from blocked IP"""
        ip_address = IDSMiddleware.get_client_ip()
        
        if IDSMiddleware.is_ip_blocked(ip_address):
            # Log the blocked request
            AuditLog.log_action(
                action='request_blocked',
                action_type='security',
                status='blocked',
                ip_address=ip_address,
                details=f'Blocked IP attempted access to {request.path}'
            )
            
            return {'error': 'Your IP address has been blocked'}, 403
