"""
AuraCrypt File Management Logic
"""

import os
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models import File, AuditLog
from app.extensions import db

class FileManager:
    """Manages file uploads, metadata, and deletion"""
    
    @staticmethod
    def save_file(user_id, file_obj, upload_folder):
        """Save an uploaded file with metadata"""
        try:
            filename = secure_filename(file_obj.filename)
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique path
            timestamp = datetime.utcnow().timestamp()
            safe_filename = f"{user_id}_{timestamp}_{filename}"
            filepath = os.path.join(upload_folder, safe_filename)
            
            # Read and save file
            file_data = file_obj.read()
            file_size = len(file_data)
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            # Create record
            new_file = File(
                owner_id=user_id,
                filename=filename,
                filepath=filepath,
                filesize=file_size,
                mimetype=file_obj.mimetype,
                file_hash=file_hash,
                metadata_json=json.dumps({
                    'original_name': filename,
                    'upload_time': datetime.utcnow().isoformat(),
                    'size_bytes': file_size
                })
            )
            
            db.session.add(new_file)
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='file_uploaded',
                action_type='file_mgmt',
                status='success',
                details=f'File ID: {new_file.id}, Filename: {filename}'
            )
            
            return new_file, None
            
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_user_files(user_id):
        """Get all files owned by a user"""
        return File.query.filter_by(owner_id=user_id).order_by(File.created_at.desc()).all()

    @staticmethod
    def delete_file(user_id, file_id):
        """Delete a file and its record"""
        try:
            file_record = File.query.filter_by(id=file_id, owner_id=user_id).first()
            if not file_record:
                return False, "File not found or unauthorized"
            
            # Delete from filesystem
            if os.path.exists(file_record.filepath):
                os.remove(file_record.filepath)
            
            # Delete from DB
            db.session.delete(file_record)
            db.session.commit()
            
            AuditLog.log_action(
                user_id=user_id,
                action='file_deleted',
                action_type='file_mgmt',
                status='success',
                details=f'File ID: {file_id}'
            )
            
            return True, None
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
