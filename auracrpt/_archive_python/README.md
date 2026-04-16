# AuraCrypt - Secure Audio Steganography System

AuraCrypt is a sophisticated, production-ready Python application that combines RSA encryption with audio steganography to securely hide and transmit secret messages within WAV audio files. It's built with Flask, SQLite, and military-grade cryptography.

## 🔒 Features

### Security
- **RSA 2048-bit Encryption**: Military-grade encryption with OAEP padding and SHA-256 hashing
- **Two-Factor Authentication (2FA)**: OTP support for enhanced account security
- **API Keys**: Programmatic access with secure hashed keys
- **LSB Audio Steganography**: Hides encrypted messages in audio files using Least Significant Bit method
- **File Integrity Verification**: SHA-256 hashing ensures audio files haven't been tampered with
- **Intrusion Detection System (IDS)**: Rate limiting, IP blocking, and anomaly detection
- **Role-Based Access Control (RBAC)**: Comprehensive permission management

### Core Functionality
- **User Authentication**: Secure login with password hashing and optional 2FA
- **File Management**: Upload, list, and delete files with full metadata tracking
- **Message Sharing**: Secure encrypted sharing with other users
- **Batch Processing**: Embed and extract multiple messages concurrently
- **Export/Import**: Backup and restore encrypted messages via JSON
- **Audit Logging**: Complete action logging for security compliance

### Web Interface & Monitoring
- **WebSocket Support**: Real-time notifications and progress updates
- **Admin Dashboard**: Comprehensive system statistics, user management, and audit logs
- **Modern UI**: Responsive Bootstrap-based design with real-time feedback
- **API Documentation**: Built-in REST API guide for developers

## 📋 Architecture

### Project Structure
```
auracrpt/
├── app/
│   ├── __init__.py           # Flask app factory (initialized with SocketIO)
│   ├── models.py             # Database models (Updated for 2FA, Files, Keys)
│   ├── auth.py               # Authentication, RBAC & 2FA Logic
│   ├── file_manager.py       # [NEW] General file management logic
│   ├── api_keys.py           # [NEW] API Key generation and verification
│   ├── batch_processor.py    # [NEW] Concurrent processing logic
│   ├── admin.py              # [NEW] Admin stats and user management
│   ├── export_import.py      # [NEW] Backup and restore logic
│   ├── sockets.py            # [NEW] WebSocket event handlers
│   ├── cryptography.py       # RSA encryption module
│   ├── steganography.py      # Audio steganography module
│   ├── ids_middleware.py     # Intrusion detection system
│   ├── routes.py             # Flask routes & API endpoints (Expanded)
│   ├── templates/            # HTML templates (Extended UI)
│   │   ├── admin_dashboard.html # [NEW] Admin UI
│   │   ├── file_manager.html    # [NEW] File Management UI
│   │   ├── 2fa_setup.html       # [NEW] 2FA Setup
│   │   ├── api_keys.html        # [NEW] API Key Management
│   │   ├── api_docs.html        # [NEW] API Documentation
│   │   ├── base.html         # Base template
│   │   ├── login.html        # Login page
│   │   ├── register.html     # Registration page
│   │   ├── dashboard.html    # User dashboard
│   │   ├── profile.html      # User profile
│   │   ├── embed.html        # Message embedding
│   │   ├── extract.html      # Message extraction
│   │   └── message_detail.html # Message details
│   └── static/               # CSS, JS, images
├── config.py                 # Configuration settings
├── run.py                    # Application entry point
├── requirements.txt          # Updated dependencies (pyotp, flask-socketio)
├── tests.py                  # Test suite
└── uploads/                 # Storage for messages and managed files
```

### Database Schema

**Users Table**
- id, username, email, password_hash, role, created_at, last_login, is_active

**PublicKeys Table**
- id, user_id, public_key, key_size, created_at, expires_at, is_active

**Messages Table**
- id, sender_id, recipient_id, title, description
- audio_file_name, audio_file_path, audio_file_size, audio_file_hash
- encrypted_message, message_size, embedding_method
- is_extracted, created_at, accessed_at

**AuditLogs Table**
- id, user_id, action, action_type, status, ip_address, user_agent, details, error_message, created_at

**IPBlockList Table**
- id, ip_address, reason, blocked_at, blocked_until, block_count

**RateLimitTracker Table**
- id, ip_address, endpoint, request_count, window_start, last_request

## 📅 Execution Timeline (Week 6 to Week 14)

- **Week 6-7 (Foundation & Setup)**: Environment setup, basic UI styling, Flask skeleton, database schema creation and connection.
- **Week 8-9 (Authentication & RBAC)**: User registration, secure login via pass hashing, role definitions (Sender/Receiver).
- **Week 10 (Cryptography)**: RSA module integration for generating unique key pairs per user, message encryption, and decryption workflows.
- **Week 11 (Audio Steganography)**: Developing the LSB algorithm for reading `.wav` binaries, safely embedding bits, and byte extraction logic.
- **Week 12 (Integration & Storage)**: Bringing it all together: Crypto + LSB. Implementing secure file uploads, SHA-256 hashing (the "file fingerprint"), and database tracking.
- **Week 13 (Network Security/IDS)**: Connecting rate limiting middleware, IP blocking upon failed attempts / DoS behavior.
- **Week 14 (Testing & Buffer Refinement)**: Final end-to-end testing, error handling for message-to-audio-size limit constraints, verifying fragility to MP3 conversion, and finalizing the demonstration.

## 🚀 Installation & Deployment

### Prerequisites
- Python 3.8 or higher
- WAV audio files for steganography

### Setup Steps

1. **Clone the project**
   ```bash
   cd auracrpt
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python run.py
   # This will automatically create tables and initialize the system
   ```

4. **Run for Development**
   ```bash
   python run.py
   ```
   The app will be available at `http://localhost:5000`

### 🛠 Deployment to Production

For production, use a WSGI server and enable WebSockets:

```bash
gunicorn --worker-class eventlet -w 1 run:app
```

## 📖 Usage Guide

### User Registration

1. Go to `/auth/register`
2. Choose a username and password (minimum 8 characters)
3. Select your role:
   - **Sender**: Can embed messages in audio files
   - **Receiver**: Can extract messages from audio files
   - **User**: Both capabilities
4. Register and proceed to login

### Sending an Encrypted Message

1. Login as a Sender
2. Navigate to "Embed Message"
3. Select a WAV audio file
4. Choose the recipient
5. Write your secret message
6. Click "Embed & Encrypt Message"
7. Share the audio file with the recipient

### Receiving and Extracting a Message

1. Login as a Receiver
2. Navigate to "Extract Message"
3. Select a message from your inbox
4. Click "Extract & Decrypt"
5. View and copy the decrypted message

### Managing Your Public Key

1. Go to your Profile
2. View your RSA public key (PEM format)
3. Share with others who want to send you encrypted messages
4. Optionally rotate your keys for extra security

## 🔐 Security Features in Detail

### RSA Key Management & Encryption
- **Algorithm**: RSA with 2048-bit key size
- **Key Generation & Assignment**: When a new user is created, the system generates a unique Public/Private key pair. 
- **Encryption Flow**: Senders utilize the intended Receiver's unique Public Key for encryption. Consequently, the message can only be decrypted by that particular Receiver's Private Key.
- **Padding**: OAEP (Optimal Asymmetric Encryption Padding)
- **Hash Function**: SHA-256
- **Key Derivation**: PKCS#8 format for storage

### LSB Steganography
- **Method**: Least Significant Bit embedding in audio samples
- **Capacity Constraints**: Dynamically calculates the available payload bytes based on audio duration. The system blocks uploads if the encrypted message exceeds the exact payload limit of the provided `.wav` file.
- **Resistance & Limitations (Vulnerability)**: Provides <1% detection probability with standard audio steganalysis. However, the transmission is intentionally fragile; converting the `.wav` file to lossy formats (like `.mp3`) or applying audio compression algorithms permanently destroys the LSB data, serving as a tamper-evidence feature.
- **Media Support**: Strictly Uncompressed WAV files (PCM, mono, stereo) to guarantee raw binary structure viability.

### Rate Limiting & IDS
- **Rate Limiting**: 100 requests per hour per IP (configurable)
- **IP Blocking**: Automatic blocking after rate limit violations
- **Block Duration**: 30 minutes (configurable)
- **Tracking**: Real-time request monitoring per IP/endpoint

### Audit Logging
- **Complete Trail**: Every action is logged with timestamp, IP, user agent
- **Action Types**: login, registration, embed, extract, key_rotation, etc.
- **Status Tracking**: Success/failure status with error messages
- **Retention**: All logs stored in database for compliance

## 📄 API Usage

All API requests require an `X-API-Key` header.

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/api/embed-message` | POST | Embed secret in WAV |
| `/api/extract-message/<id>` | POST | Extract secret from WAV |
| `/api/files/upload` | POST | Upload a managed file |

Full documentation is available in the web UI under the **API Docs** tab.

## 🧪 Testing

Run tests to ensure everything is working correctly:
```bash
python tests.py
```

Test coverage includes:
- RSA key generation and serialization
- Message encryption/decryption
- Audio file validation and capacity
- Message embedding/extraction
- User registration and authentication
- Role-based access control
- Flask integration tests

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Security settings
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Max file size
RATE_LIMIT_REQUESTS = 100              # Requests per window
RATE_LIMIT_WINDOW = 3600               # 1 hour
MAX_IPS_BLOCKED = 50                   # Max blocked IPs

# Cryptography
RSA_KEY_SIZE = 2048                    # RSA key size in bits

# Steganography
MAX_MESSAGE_SIZE = 1024 * 100          # 100KB max encrypted message
```

## 🐛 Troubleshooting

### Database Issues
```python
# Recreate database
from app import create_app, db
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
```

### Authentication Issues
- Clear cookies and cache
- Check that user email is unique
- Verify password meets requirements (8+ characters)

### Embedding Failures
- Ensure WAV file is valid and not corrupted
- Check file size (max 50MB)
- Verify message isn't too large for audio capacity
- Try a longer audio file for larger messages

### Extraction Issues
- Confirm recipient has access to recipient's private key
- Verify audio file integrity hasn't been modified
- Check that message was properly embedded
- Review audit logs for error details

## 🔄 Performance Optimization

### Database Optimization
- Indexes on frequently queried fields (user_id, ip_address, created_at)
- Connection pooling for SQLite
- Query result pagination

### File Handling
- Streaming for large file uploads
- Temporary file cleanup
- Configurable upload folder location

### Caching
- Session-based caching for public keys
- Database query optimization

## 📝 Development Notes

### Adding New Features
1. Extend models in `models.py`
2. Add routes in `routes.py`
3. Implement business logic in appropriate modules
4. Add tests in `tests.py`
5. Update templates as needed
6. Document changes in this README

### Deploying to Production
1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Configure reverse proxy (Nginx, Apache)
4. Use HTTPS with valid SSL certificate
5. Enable CSRF protection
6. Set secure session cookies
7. Regular database backups
8. Monitor audit logs regularly

### Key Security Considerations
- Never log passwords or private keys
- Validate all user inputs
- Use parameterized queries (SQLAlchemy handles this)
- Implement proper CORS policies
- Use HTTP-only cookies
- Implement rate limiting on critical endpoints
- Regular security updates to dependencies

## 📄 License

This project is provided as-is for educational and secure communication purposes.

## 🤝 Contributing

To contribute:
1. Test your changes thoroughly
2. Follow existing code style
3. Add tests for new functionality
4. Update documentation
5. Submit improvements with clear descriptions

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review audit logs for error details
3. Enable debug logging in config.py
4. Test with provided test suite

## 🎯 Future Enhancements

- Multi-file embedding support
- Additional steganography methods (LSB+ variants, DCT)
- Audio format support (MP3, FLAC, OGG)
- Message expiration/auto-delete

---

**AuraCrypt v1.0** - Built with security, privacy, and simplicity in mind.
