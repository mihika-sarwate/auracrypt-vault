"""
AuraCrypt WebSocket Support
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from flask import request

socketio = SocketIO(cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        emit('status', {'msg': 'Connected to AuraCrypt Live'})

@socketio.on('subscribe_progress')
def handle_subscribe(data):
    """Subscribe to progress updates for a specific task"""
    task_id = data.get('task_id')
    if task_id:
        join_room(f"task_{task_id}")

def notify_user(user_id, event, data):
    """Send real-time notification to a specific user"""
    socketio.emit(event, data, room=f"user_{user_id}")

def update_progress(task_id, progress, message):
    """Update progress for a long-running task"""
    socketio.emit('progress', {
        'task_id': task_id,
        'progress': progress,
        'message': message
    }, room=f"task_{task_id}")
