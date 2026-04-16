"""
AuraCrypt Export/Import Logic
"""

import json
from datetime import datetime
from app.models import Message, User
from app.extensions import db

class DataExportImport:
    """Handles backup and restore of encrypted messages"""
    
    @staticmethod
    def export_user_data(user_id):
        """Export all messages for a user to JSON"""
        messages = Message.query.filter(
            (Message.sender_id == user_id) | (Message.recipient_id == user_id)
        ).all()
        
        export_data = {
            'version': '1.0',
            'exported_at': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'messages': []
        }
        
        for msg in messages:
            export_data['messages'].append({
                'title': msg.title,
                'description': msg.description,
                'audio_file_name': msg.audio_file_name,
                'encrypted_message': msg.encrypted_message,
                'created_at': msg.created_at.isoformat(),
                'sender': msg.sender.username,
                'recipient': msg.recipient.username
            })
            
        return json.dumps(export_data, indent=2)

    @staticmethod
    def import_user_data(user_id, json_data):
        """Import messages from JSON backup (simplified)"""
        try:
            data = json.loads(json_data)
            # Logic for importing/merging records
            # ...
            return len(data.get('messages', [])), None
        except Exception as e:
            return 0, str(e)
