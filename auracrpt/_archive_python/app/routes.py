"""
AuraCrypt Flask Routes
Defines all API endpoints and web routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

from app.models import User, Message, AuditLog, PublicKey, File, APIKey
from app.extensions import db
from app.auth import AuthenticationManager, RoleBasedAccessControl
from app.cryptography import MessageEncryption, FileIntegrity
from app.steganography import AudioSteganography, SteganographyValidator
from app.ids_middleware import IDSMiddleware, RateLimitDecorator
from app.file_manager import FileManager
from app.api_keys import APIKeyManager
from app.batch_processor import BatchProcessor
from app.admin import AdminManager
from app.export_import import DataExportImport
from app.sockets import notify_user
from config import Config

# Create blueprints
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')


# ==================== AUTHENTICATION ROUTES ====================

@auth_bp.route('/register', methods=['GET', 'POST'])
@RateLimitDecorator.limit_request_rate(max_requests=10, window_seconds=3600)
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'user')
        
        # Validate
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
        
        # Register user
        user, error = AuthenticationManager.register_user(username, email, password, role)
        
        if error:
            flash(error, 'error')
            AuditLog.log_action(
                action='registration_failed',
                action_type='registration',
                status='failed',
                details=f'Username: {username}, Error: {error}'
            )
            return redirect(url_for('auth.register'))
        
        flash('Registration successful! Please log in.', 'success')
        AuditLog.log_action(
            user_id=user.id,
            action='user_registered',
            action_type='registration',
            status='success'
        )
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@RateLimitDecorator.limit_request_rate(max_requests=20, window_seconds=3600)
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = AuthenticationManager.authenticate_user(username, password)
        
        if user:
            login_user(user, remember=request.form.get('remember', False))
            AuditLog.log_action(
                user_id=user.id,
                action='user_login',
                action_type='login',
                status='success'
            )
            return redirect(url_for('main.dashboard'))
        
        flash('Invalid username or password', 'error')
        AuditLog.log_action(
            action='login_failed',
            action_type='login',
            status='failed',
            details=f'Username: {username}'
        )
        return redirect(url_for('auth.login'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    AuditLog.log_action(
        user_id=current_user.id,
        action='user_logout',
        action_type='logout',
        status='success'
    )
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))


# ==================== MAIN ROUTES ====================

@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.created_at.desc()).limit(10).all()
    
    user_public_key = AuthenticationManager.get_user_public_key(current_user.id)
    
    return render_template('dashboard.html', messages=messages, user_public_key=user_public_key)


@main_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    user = current_user
    public_key = AuthenticationManager.get_user_public_key(user.id)
    message_count = Message.query.filter(
        (Message.sender_id == user.id) | (Message.recipient_id == user.id)
    ).count()
    
    return render_template('profile.html', 
                         message_count=message_count,
                         public_key=public_key)


@main_bp.route('/embed')
@login_required
def embed_page():
    """Message embedding page"""
    recipients = User.query.filter(User.id != current_user.id).all()
    return render_template('embed.html', recipients=recipients)


@main_bp.route('/extract')
@login_required
def extract_page():
    """Message extraction page"""
    messages = Message.query.filter_by(recipient_id=current_user.id).all()
    return render_template('extract.html', messages=messages)


@main_bp.route('/messages/<message_id>')
@login_required
def view_message(message_id):
    """View message details"""
    message = Message.query.get(message_id)
    
    if not message:
        flash('Message not found', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check authorization
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('You do not have permission to view this message', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('message_detail.html', message=message)


# ==================== FILE MANAGEMENT ROUTES ====================

@main_bp.route('/files')
@login_required
def list_files():
    """List user files"""
    files = FileManager.get_user_files(current_user.id)
    return render_template('file_manager.html', files=files)


@main_bp.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a file"""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('main.list_files'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('main.list_files'))
    
    new_file, error = FileManager.save_file(current_user.id, file, Config.UPLOAD_FOLDER)
    if error:
        flash(f'Upload failed: {error}', 'error')
    else:
        flash('File uploaded successfully', 'success')
        notify_user(current_user.id, 'notification', {'msg': 'File upload complete'})
    
    return redirect(url_for('main.list_files'))


@main_bp.route('/files/delete/<file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete a file"""
    success, error = FileManager.delete_file(current_user.id, file_id)
    if success:
        flash('File deleted successfully', 'success')
    else:
        flash(f'Delete failed: {error}', 'error')
    
    return redirect(url_for('main.list_files'))


# ==================== 2FA ROUTES ====================

@main_bp.route('/2fa/setup')
@login_required
def setup_2fa():
    """2FA setup page"""
    if current_user.is_2fa_enabled:
        flash('2FA is already enabled', 'info')
        return redirect(url_for('main.profile'))
    
    setup_data, error = AuthenticationManager.setup_2fa(current_user.id)
    return render_template('2fa_setup.html', setup_data=setup_data)


@main_bp.route('/2fa/enable', methods=['POST'])
@login_required
def enable_2fa():
    """Verify and enable 2FA"""
    token = request.form.get('token')
    success, error = AuthenticationManager.enable_2fa(current_user.id, token)
    
    if success:
        flash('2FA enabled successfully', 'success')
        return redirect(url_for('main.profile'))
    
    flash(error, 'error')
    return redirect(url_for('main.setup_2fa'))


# ==================== API KEY ROUTES ====================

@main_bp.route('/api-keys')
@login_required
def manage_api_keys():
    """API key management page"""
    keys = APIKey.query.filter_by(user_id=current_user.id).all()
    return render_template('api_keys.html', keys=keys)


@main_bp.route('/api-keys/generate', methods=['POST'])
@login_required
def generate_api_key():
    """Generate a new API key"""
    name = request.form.get('name', 'My API Key')
    api_key, key_record = APIKeyManager.generate_key(current_user.id, name)
    
    if api_key:
        flash(f'API Key generated: {api_key}. SAVE THIS NOW as it won\'t be shown again.', 'success')
    else:
        flash('Failed to generate API Key', 'error')
    
    return redirect(url_for('main.manage_api_keys'))


# ==================== ADMIN ROUTES ====================

@main_bp.route('/admin')
@login_required
@RoleBasedAccessControl.require_role('admin', 'user') # For demo, allow 'user' if they have a special flag, but usually 'admin'
def admin_dashboard():
    """Admin dashboard"""
    # Simple check for now
    if current_user.username != 'admin' and current_user.role != 'admin':
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))
        
    stats = AdminManager.get_system_stats()
    users = AdminManager.get_user_management_data()
    return render_template('admin_dashboard.html', stats=stats, users=users)


@main_bp.route('/api-docs')
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html')


# ==================== API ROUTES ====================

@api_bp.route('/embed-message', methods=['POST'])
@login_required
def api_embed_message():
    """Embed message into audio file"""
    try:
        # Validate request
        if 'file' not in request.files or 'message' not in request.form:
            return jsonify({'error': 'Missing file or message'}), 400
        
        audio_file = request.files['file']
        message_text = request.form.get('message', '').strip()
        recipient_id = request.form.get('recipient_id', '').strip()
        title = request.form.get('title', 'Unnamed Message').strip()
        description = request.form.get('description', '').strip()
        
        # Validate inputs
        if not audio_file.filename or not message_text or not recipient_id:
            return jsonify({'error': 'Invalid input'}), 400
        
        if len(message_text) > Config.MAX_MESSAGE_SIZE:
            return jsonify({'error': 'Message too large'}), 413
        
        # Check recipient exists
        recipient = User.query.get(recipient_id)
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        # Validate audio file
        filename = secure_filename(audio_file.filename)
        if not filename.lower().endswith('.wav'):
            return jsonify({'error': 'Only WAV files are supported'}), 400
        
        # Read audio data
        audio_data = audio_file.read()
        
        if not SteganographyValidator.is_valid_wav_file(audio_data):
            return jsonify({'error': 'Invalid WAV file'}), 400
        
        # Get recipient's public key
        recipient_key = AuthenticationManager.get_user_public_key(recipient_id)
        if not recipient_key:
            return jsonify({'error': 'Recipient has no public key'}), 400
        
        # Encrypt message
        encryption = MessageEncryption()
        encrypted_message_hex = encryption.encrypt_message_hex(message_text, recipient_key.public_key)
        
        # Embed encrypted message in audio
        encrypted_bytes = bytes.fromhex(encrypted_message_hex)
        
        # Check capacity
        capacity = AudioSteganography.get_audio_capacity(audio_data)
        if len(encrypted_bytes) > capacity:
            return jsonify({'error': f'Encrypted message too large for audio file. Max: {capacity} bytes'}), 413
        
        # Embed message
        modified_audio = AudioSteganography.encode_message_to_audio(audio_data, encrypted_bytes)
        
        # Calculate file hash
        file_hash = FileIntegrity.calculate_file_hash(modified_audio)
        
        # Save to uploads folder
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        safe_filename = f"{current_user.id}_{datetime.utcnow().timestamp()}_{filename}"
        file_path = os.path.join(Config.UPLOAD_FOLDER, safe_filename)
        
        with open(file_path, 'wb') as f:
            f.write(modified_audio)
        
        # Create message record
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            title=title,
            description=description,
            audio_file_name=filename,
            audio_file_path=file_path,
            audio_file_size=len(modified_audio),
            audio_file_hash=file_hash,
            encrypted_message=encrypted_message_hex,
            message_size=len(encrypted_bytes),
            embedding_method='lsb'
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action='message_embedded',
            action_type='embed',
            status='success',
            details=json.dumps({
                'message_id': message.id,
                'recipient_id': recipient_id,
                'message_size': len(encrypted_bytes),
                'audio_size': len(modified_audio)
            })
        )
        
        return jsonify({
            'success': True,
            'message_id': message.id,
            'message': 'Message embedded successfully'
        }), 201
    
    except Exception as e:
        AuditLog.log_action(
            user_id=current_user.id,
            action='message_embed_failed',
            action_type='embed',
            status='failed',
            error_message=str(e)
        )
        return jsonify({'error': f'Embedding failed: {str(e)}'}), 500


@api_bp.route('/extract-message/<message_id>', methods=['POST'])
@login_required
def api_extract_message(message_id):
    """Extract message from audio file"""
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check authorization
        if message.recipient_id != current_user.id:
            return jsonify({'error': 'You do not have permission to extract this message'}), 403
        
        # Read audio file
        with open(message.audio_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Verify file integrity
        if not FileIntegrity.verify_file_integrity(audio_data, message.audio_file_hash):
            AuditLog.log_action(
                user_id=current_user.id,
                action='extraction_failed',
                action_type='extract',
                status='failed',
                details=f'Message ID: {message_id}, Reason: File integrity check failed'
            )
            return jsonify({'error': 'File integrity check failed. File may be corrupted.'}), 400
        
        # Extract encrypted message
        encrypted_bytes = AudioSteganography.decode_message_from_audio(audio_data)
        encrypted_message_hex = encrypted_bytes.hex()
        
        # Decrypt message
        # Note: In production, private keys should be stored securely
        # For now, we'll return the encrypted message as-is for security
        decrypted_message = "Message extracted successfully. Private key decryption would occur in a secure environment."
        
        # Mark as extracted
        message.is_extracted = True
        message.accessed_at = datetime.utcnow()
        db.session.commit()
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='message_extracted',
            action_type='extract',
            status='success',
            details=f'Message ID: {message_id}'
        )
        
        return jsonify({
            'success': True,
            'message': decrypted_message,
            'encrypted_hex': encrypted_message_hex[:100] + '...',  # Preview
        }), 200
    
    except Exception as e:
        AuditLog.log_action(
            user_id=current_user.id,
            action='extraction_failed',
            action_type='extract',
            status='failed',
            error_message=str(e)
        )
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500


@api_bp.route('/download-audio/<message_id>')
@login_required
def api_download_audio(message_id):
    """Download audio file"""
    try:
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'error': 'Message not found'}), 404
        
        # Check authorization
        if message.sender_id != current_user.id and message.recipient_id != current_user.id:
            return jsonify({'error': 'You do not have permission to download this file'}), 403
        
        AuditLog.log_action(
            user_id=current_user.id,
            action='file_downloaded',
            action_type='download',
            status='success',
            details=f'Message ID: {message_id}'
        )
        
        return send_file(
            message.audio_file_path,
            as_attachment=True,
            download_name=message.audio_file_name,
            mimetype='audio/wav'
        )
    
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@api_bp.route('/users/<username>/public-key')
def api_get_public_key(username):
    """Get user's public key (public endpoint for encryption)"""
    try:
        user = AuthenticationManager.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        public_key = AuthenticationManager.get_user_public_key(user.id)
        
        if not public_key:
            return jsonify({'error': 'User has no public key'}), 404
        
        return jsonify({
            'username': user.username,
            'public_key': public_key.public_key,
            'key_size': public_key.key_size
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/audit-logs', methods=['GET'])
@login_required
@RoleBasedAccessControl.require_role('user')
def api_audit_logs():
    """Get audit logs for current user"""
    logs = AuditLog.query.filter_by(user_id=current_user.id).order_by(
        AuditLog.created_at.desc()
    ).limit(50).all()
    
    return jsonify([{
        'id': log.id,
        'action': log.action,
        'action_type': log.action_type,
        'status': log.status,
        'created_at': log.created_at.isoformat()
    } for log in logs]), 200
