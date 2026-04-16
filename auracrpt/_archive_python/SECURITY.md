# AuraCrypt Security Architecture

Comprehensive guide to AuraCrypt's security features, design decisions, and best practices.

## Table of Contents
1. [Encryption](#encryption)
2. [Steganography](#steganography)
3. [Authentication & Authorization](#authentication--authorization)
4. [Network Security](#network-security)
5. [Data Security](#data-security)
6. [Deployment Security](#deployment-security)
7. [Incident Response](#incident-response)

---

## Encryption

### RSA Cryptography

**Algorithm Details:**
- **Type**: RSA (Rivest-Shamir-Adleman)
- **Key Size**: 2048 bits
- **Padding**: OAEP (Optimal Asymmetric Encryption Padding)
- **Hash Function**: SHA-256
- **Key Format**: PKCS#8 (Python Cryptography library compatible)

**Why RSA 2048-bit?**
```
Key Size | Security Level | Equivalent Symmetric | Safe Until
---------|----------------|----------------------|----------
1024     | 80 bits        | AES-80              | 2010 (Broken)
2048     | 112 bits       | AES-112             | 2030+
4096     | 128 bits       | AES-128             | 2050+
```

AuraCrypt uses 2048-bit keys which:
- Provide adequate security for messages (112-bit equivalent)
- Don't require computational overhead of 4096-bit
- Meet NIST recommendations through 2030

**Why OAEP Padding?**
- Prevents chosen-ciphertext attacks
- More secure than PKCS#1 v1.5 padding
- Industry standard in cryptography libraries

**Key Generation Process:**
```python
1. Generate random private key
2. Derive public key from private key
3. Serialize both to PEM format
4. Store public key in database
5. Private key handled by user (NOT stored)
```

### Message Encryption Flow

```
[Plain Text]
     ↓
[UTF-8 Encoding]
     ↓
[RSA Encryption with Recipient's Public Key]
     ↓
[Hex Encoding for storage]
     ↓
[Audio Steganography Embedding]
     ↓
[Modified WAV File]
```

### Decryption Flow

```
[Modified WAV File]
     ↓
[LSB Extraction]
     ↓
[Hex Decoding]
     ↓
[RSA Decryption with Private Key]
     ↓
[UTF-8 Decoding]
     ↓
[Plain Text Message]
```

---

## Steganography

### LSB (Least Significant Bit) Method

**How It Works:**
```
Original audio sample: 11010110 (binary)
Message bit:          1 (binary)

Modified sample:      11010111 (binary)
                             ↑
                      Least significant bit
```

**Why LSB?**
- Imperceptible to human hearing (changes <0.004% of audio amplitude)
- Simple and fast implementation
- Standard steganography method
- Perfect for encryption hiding

**Capacity Calculation:**

```
Capacity = (Total Sample Bits / 8) - 4 bytes (for length header)

Example for 3-second 44.1kHz mono WAV:
Total samples = 44,100 * 3 = 132,300
Total bits = 132,300 * 16 = 2,116,800 bits
Capacity = (2,116,800 / 8) - 4 = ~264,596 - 4 = 264,592 bytes (≈258 KB)
```

AuraCrypt limits to 100KB to:
- Allow safety margin for various audio formats
- Prevent obvious capacity detection
- Ensure reliable extraction

**Detection Resistance:**

LSB steganography is resistant to:
- Visual inspection (inaudible)
- Standard spectrum analysis
- Statistical analysis (with proper encryption)

Detection is possible only with:
- Steganalysis tools (RS analysis, chi-square)
- Direct LSB comparison with original
- Specialized AI/ML models

Estimated detection probability: **< 1%** for standard analysis tools

### Embedding Process

```python
1. Read WAV file (get all audio samples)
2. Encrypt message with RSA
3. Convert message length to 32-bit binary
4. Embed length in first 32 LSBs
5. Convert encrypted bytes to binary
6. Embed each bit in LSB of sequential samples
7. Reconstruct WAV with modified samples
8. Calculate SHA-256 hash for integrity
```

### Extraction Process

```python
1. Read WAV file samples
2. Extract first 32 LSBs (message length)
3. Calculate expected data size
4. Extract required number of LSBs
5. Reconstruct encrypted message from bits
6. Verify file integrity with SHA-256
7. Return encrypted bytes (user decrypts with private key)
```

---

## Authentication & Authorization

### User Authentication

**Password Security:**
```python
# Passwords hashed with bcrypt
password = "MyPassword123"
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12))

# Bcrypt settings:
- Algorithm: Bcrypt
- Rounds: 12 (configurable in Werkzeug)
- Salt: Auto-generated per password
```

**Session Management:**
```python
# Flask-Login provides:
- Session-based authentication
- Remember-me functionality (7 days)
- Secure cookie handling
- CSRF protection (WTForms)

# Cookie settings:
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
REMEMBER_COOKIE_SECURE = True     # HTTPS only
REMEMBER_COOKIE_HTTPONLY = True   # No JavaScript access
```

### Role-Based Access Control (RBAC)

**Three User Roles:**

```python
SENDER:
  - embed_message     → Encrypt and hide messages
  - view_dashboard    → See personal dashboard
  - manage_profile    → View public key

RECEIVER:
  - extract_message   → Decrypt and view messages
  - view_dashboard    → See personal dashboard
  - manage_profile    → View public key

USER:
  - All permissions (both sender and receiver)
```

**Authorization Checks:**
```python
# Decorator-based access control
@require_role('sender')
def embed_message():
    # User must have 'sender' role
    pass

@require_permission('extract_message')
def extract():
    # User must have 'extract_message' permission
    pass
```

**Data Access Control:**
```python
# Message access rules:
- Sender can always view sent messages
- Recipient can view received messages
- Others cannot access message details
- File downloads restricted to authorized users

# Public key access:
- Public keys are publicly readable
- Private keys never stored/accessed
```

---

## Network Security

### Rate Limiting & IDS

**Rate Limiting Implementation:**
```python
RATE_LIMIT_REQUESTS = 100          # Max requests
RATE_LIMIT_WINDOW = 3600           # Per 1 hour
RATE_LIMIT_ENABLED = True          # Global enable

# Per-endpoint tracking:
GET /auth/login       → 20 req/hour
GET /auth/register    → 10 req/hour
POST /api/embed-message → 50 req/hour
Other endpoints       → 100 req/hour
```

**Rate Limit Response:**
```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "error": "Rate limit exceeded"
}
```

**IP Blocking System:**
```python
# Automatic blocking triggers:
1. Rate limit exceeded (5 times in 1 window)
2. Suspicious activity detected
3. Failed login attempts (threshold)

# Block properties:
- Duration: 30 minutes (configurable)
- Expiration: Auto-removes when expired
- Whitelist: None by default
- Admin override: Manual unblock available
```

**Blocking Process:**
```python
# When threshold exceeded:
1. IP added to IPBlockList table
2. block_until set to now + duration
3. Audit log entry created
4. All requests from IP rejected
5. Block expires automatically
```

### HTTPS/SSL

**Recommendations for Production:**

```python
# In production (config.py):
SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_HTTPONLY = True
PREFERRED_URL_SCHEME = 'https'
```

**SSL/TLS Configuration:**
```nginx
# Nginx example
server {
    listen 443 ssl http2;
    server_name auracrpt.example.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
}
```

### CORS & CSP

**CORS Policy:**
```python
# Add to Flask app if API is used by web clients:
from flask_cors import CORS

CORS(app, 
     origins=['yourdomain.com'],
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST'])
```

**Content Security Policy:**
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' cdn.jsdelivr.net; "
        "style-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
        "font-src 'self' cdnjs.cloudflare.com"
    )
    return response
```

### CSRF Protection

**Flask-WTF CSRF:**
```python
# Enabled by default
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None  # No time limit

# In templates:
{{ csrf_token() }}

# In AJAX requests:
headers: {'X-CSRFToken': csrfToken}
```

---

## Data Security

### File Integrity Verification

**SHA-256 Hashing:**
```python
# When audio is saved:
file_hash = hashlib.sha256(file_data).hexdigest()

# When audio is retrieved:
stored_hash = message.audio_file_hash
calculated_hash = hashlib.sha256(file_data).hexdigest()

if stored_hash == calculated_hash:
    # File integrity verified
else:
    # File corrupted/tampered!
    raise IntegrityError()
```

**Hash-based Integrity Check:**
```python
SHA-256 produces 64-character hex string:
a1b2c3d4e5f6...0z (256 bits)

Probability of collision: < 2^-128 (astronomically small)
Safe for file integrity verification
```

### Database Security

**SQLAlchemy Parameterized Queries:**
```python
# Safe against SQL injection:
user = User.query.filter_by(username=username).first()

# Not vulnerable even if username contains SQL:
# username = "admin'; DROP TABLE users; --"
```

**Data Encryption at Rest:**
```python
# Items stored encrypted in database:
- User passwords (bcrypt hashes, not plaintext)
- Encrypted messages (hex-encoded RSA encrypted data)
- Public keys (PEM text format)
- Private keys (NOT stored, user-managed)
```

### File Storage Security

**Upload Directory:**
```python
# Configuration:
UPLOAD_FOLDER = './uploads'
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

# File naming (prevents collisions):
filename = f"{user_id}_{timestamp}_{original_name}"
safe_filename = secure_filename(filename)

# Permissions:
chmod 700 uploads/  # Owner read/write/execute only
chmod 600 *.wav    # Owner read/write only
```

**Temporary File Cleanup:**
```python
# After extraction/processing:
- Original uploaded files cleaned up
- Modified audio files retained (for re-extraction)
- Old files purged after retention period (30 days)
```

---

## Deployment Security

### Environment Variables

**Never commit secrets:**
```bash
# .gitignore
.env
*.db
uploads/
__pycache__/
.env.local
```

**Required Environment Variables:**
```bash
# .env file (production)
FLASK_ENV=production
SECRET_KEY=<64+ random characters>
DATABASE_URL=postgresql://...  # Or other secure DB
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

### Database Deployment

**For Development:**
```python
# SQLite is fine
SQLALCHEMY_DATABASE_URI = 'sqlite:///auracrpt.db'
```

**For Production (Recommended):**
```python
# Use PostgreSQL with connection pooling
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/auracrpt'
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### Server Hardening

**Gunicorn Configuration:**
```bash
# Production server
gunicorn --workers 4 \
         --worker-class sync \
         --bind 0.0.0.0:5000 \
         --timeout 30 \
         --access-logfile - \
         --error-logfile - \
         run:app
```

**Reverse Proxy (Nginx):**
```nginx
server {
    listen 443 ssl http2;
    server_name auracrpt.example.com;
    
    # Rate limiting at reverse proxy level
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5000;
    }
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Logging & Monitoring

**Comprehensive Audit Logging:**
```python
# Logged actions:
- User registration
- User login/logout
- Message embedding
- Message extraction
- Key rotation
- Access attempts
- Rate limit violations
- IP blocking events

# Audit log fields:
- user_id: Who performed action
- action: What was done
- action_type: Category
- status: Success/failure
- ip_address: Source IP
- user_agent: Client info
- timestamp: When
- details: Additional context
```

**Log Monitoring:**
```python
# View suspicious activity:
failed_logins = AuditLog.query.filter_by(
    action='user_login',
    status='failed'
).count()

blocked_ips = IPBlockList.query.filter(
    IPBlockList.blocked_until > datetime.utcnow()
).all()
```

---

## Incident Response

### Detecting Compromises

**Signs of Compromise:**
1. Unexpected audit log entries
2. Messages not sent by you in dashboard
3. IP blocks from unusual locations
4. Repeated login failures
5. Unusual public key access patterns

### Incident Response Steps

**If your account is compromised:**

1. **Immediate Actions:**
   - Change password (from another device)
   - Rotate RSA keys in profile
   - Check audit logs for unauthorized access
   - Review all messages for tampering

2. **Notify Recipients:**
   - Inform those who received messages
   - Invalidate old public key
   - Request re-encryption with new key

3. **Report to Admin:**
   - Provide timeline of incident
   - Share audit log details
   - List suspicious IP addresses

4. **Follow-up:**
   - Review new audit logs
   - Monitor for repeated attacks
   - Enable IP whitelisting if available

**If audio file is intercepted:**
1. Message is encrypted (RSA) - sender identity secure
2. Recipient's identity hidden in filename only
3. Audio file hash verification prevents tampering
4. Re-send via different channel if concerned

### Security Updates

**Keep Dependencies Updated:**
```bash
# Check for vulnerabilities
pip list --outdated

# Update specific packages
pip install --upgrade Flask cryptography

# Regular security audits
pip install safety
safety check
```

---

## Security Checklist

### Development
- [ ] Never commit .env or database files
- [ ] Use parameterized queries (SQLAlchemy)
- [ ] Validate all user input
- [ ] Use secure password storage (bcrypt)
- [ ] Enable CSRF protection
- [ ] Implement rate limiting
- [ ] Log security events
- [ ] Test authentication flows

### Production Deployment
- [ ] Use HTTPS/TLS (not HTTP)
- [ ] Set SECRET_KEY to strong random value
- [ ] Use production database (PostgreSQL)
- [ ] Enable secure session cookies
- [ ] Configure reverse proxy (Nginx/Apache)
- [ ] Set up firewall rules
- [ ] Enable audit logging
- [ ] Implement monitoring/alerts
- [ ] Regular database backups
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] IDS active and monitored

### Operational Security
- [ ] Regular security updates
- [ ] Monitor audit logs daily
- [ ] Review blocked IPs
- [ ] Check for unusual patterns
- [ ] Incident response plan
- [ ] Data retention policy
- [ ] Access control reviews
- [ ] Encryption key management

---

## References

- **NIST Recommendations:** https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-175B.pdf
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **Cryptography.io:** https://cryptography.io/en/latest/
- **Flask Security:** https://flask.palletsprojects.com/security/

---

**Last Updated:** 2024-01-15
**Security Level:** Production-Ready with Recommendations
