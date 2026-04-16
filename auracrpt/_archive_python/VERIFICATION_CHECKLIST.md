# AuraCrypt - Verification Checklist

## Pre-Deployment Verification

Use this checklist to verify that AuraCrypt is fully working and ready to deploy.

---

## ✅ Phase 1: Installation Verification

- [ ] Run: `pip install -r requirements.txt`
  - Expected: All 8 packages install successfully
  - Time: ~1-2 minutes

- [ ] Run: `python init_db.py`
  - Expected: Database created with 7 tables and 3 test users
  - Output should show:
    ```
    Creating database tables...
    Database tables created successfully!
    Seeding test users...
    ✓ Created alice (sender)
    ✓ Created bob (receiver)
    ✓ Created charlie (user)
    ```

- [ ] Verify database file exists: `ls -la auracrpt.db`
  - Expected: File size > 20KB

- [ ] Verify upload folder: `mkdir -p uploads`
  - Expected: Folder created (if doesn't exist)

---

## ✅ Phase 2: Component Validation

- [ ] Run: `python validate.py`
  - Expected: All 6 tests pass
  ```
  ✓ PASS: Dependencies
  ✓ PASS: Flask App
  ✓ PASS: Database
  ✓ PASS: Cryptography
  ✓ PASS: Authentication
  ✓ PASS: Steganography
  
  Total: 6/6 tests passed
  🎉 All tests passed! AuraCrypt is ready to use.
  ```

---

## ✅ Phase 3: Test Suite Execution

- [ ] Run: `python test_integration.py`
  - Expected: 19 tests pass
  - Test categories:
    - [ ] TestAuthentication: 5 tests
    - [ ] TestCryptography: 5 tests
    - [ ] TestSteganography: 5 tests
    - [ ] TestDatabase: 3 tests
    - [ ] TestEndToEnd: 1 test

---

## ✅ Phase 4: Application Startup

- [ ] Run: `python run.py`
  - Expected console output:
  ```
   * Serving Flask app 'app'
   * Debug mode: on
   * Running on http://0.0.0.0:5000
  ```

- [ ] Wait 3-5 seconds for app to fully start

- [ ] Open browser: `http://localhost:5000`
  - Expected: Redirects to login page

---

## ✅ Phase 5: Web Interface Testing

### Login Page
- [ ] Page loads without errors
- [ ] Form has: username, password, remember me, login button
- [ ] Styling looks correct (Bootstrap 5)

### Registration
- [ ] Click "Register here" link (or go to `/auth/register`)
- [ ] Form has: username, email, password, confirm password, role selector
- [ ] Register with test account:
  ```
  Username: testuser
  Email: testuser@example.com
  Password: password123
  Confirm: password123
  Role: sender
  ```
- [ ] Success message appears
- [ ] Can login with new account

### Authentication Tests
- [ ] Test with existing user:
  ```
  Username: alice
  Password: password123
  ```
- [ ] Login successful - redirects to dashboard
- [ ] Test wrong password - error message shown
- [ ] Test nonexistent user - error message shown

### Dashboard
- [ ] Page loads (at `/dashboard`)
- [ ] Shows "Welcome" message
- [ ] Shows recent messages (initially empty)
- [ ] Navigation menu visible
- [ ] Logout link present

### Profile Page
- [ ] Click "Profile" in navbar
- [ ] Shows current user info
- [ ] Shows public key
- [ ] Shows message statistics

### Embed Message Page
- [ ] Click "Embed Message" in navbar
- [ ] Form has: recipient selector, title, description, message text, file upload
- [ ] Can select recipient from dropdown
- [ ] File upload works

### Extract Message Page
- [ ] Click "Extract Message" in navbar
- [ ] Shows list of received messages (empty initially)
- [ ] Message listing works correctly

---

## ✅ Phase 6: API Testing (curl/Postman)

### Public Key Endpoint
```bash
curl http://localhost:5000/api/users/alice/public-key

# Expected response:
{
  "username": "alice",
  "public_key": "-----BEGIN PUBLIC KEY-----...",
  "key_size": 2048
}
```

### Login Session
```bash
# Get session cookie
curl -c cookies.txt -X POST http://localhost:5000/auth/login \
  -d "username=alice&password=password123"

# Verify logged in
curl -b cookies.txt http://localhost:5000/dashboard

# Expected: Dashboard HTML returned
```

---

## ✅ Phase 7: Database Verification

- [ ] Run Python shell:
```python
python run.py shell

# Verify tables
>>> from app.models import User, Message, AuditLog
>>> User.query.count()
# Expected: >= 3 (alice, bob, charlie, testuser)

>>> Message.query.count()
# Expected: 0 (no messages yet)

>>> AuditLog.query.count()
# Expected: > 0 (registration logs)

# Check specific user
>>> alice = User.query.filter_by(username='alice').first()
>>> alice.username
'alice'
>>> alice.role
'sender'
>>> alice.check_password('password123')
True

# Check public key
>>> alice.public_key_record
<PublicKey for alice>
>>> len(alice.public_key_record.public_key) > 1000
True  # Should be long PEM string

# Check audit logs
>>> logs = AuditLog.query.filter_by(user_id=alice.id).all()
>>> len(logs) > 0
True
```

---

## ✅ Phase 8: Security Verification

### Rate Limiting
- [ ] Make rapid requests to trigger rate limit:
```bash
for i in {1..101}; do
  curl http://localhost:5000/auth/register
done
```
- [ ] After 100 requests, should get 429 error
- [ ] Check database for blocked IP:
```python
>>> from app.models import IPBlockList
>>> IPBlockList.query.all()
# Should show your IP blocked
```

### CSRF Protection
- [ ] Logout and go to login page
- [ ] Inspect form - should have CSRF token:
```html
<input type="hidden" name="csrf_token" value="...">
```

### Password Hashing
- [ ] Verify passwords are hashed in database:
```python
>>> from app.models import User
>>> alice = User.query.filter_by(username='alice').first()
>>> alice.password_hash[:6]
'$2b$12'  # Should be bcrypt hash, not plaintext
>>> alice.password_hash == 'password123'
False  # Should not match plaintext
```

---

## ✅ Phase 9: Cryptography Verification

```python
from app.cryptography import RSAKeyManager, MessageEncryption

# Generate keypair
manager = RSAKeyManager(2048)
private_key, public_key = manager.generate_keypair()

# Serialize
public_pem = manager.serialize_public_key(public_key)
private_pem = manager.serialize_private_key(private_key)

# Test encryption/decryption
encryption = MessageEncryption()
message = "Secret message"
encrypted = encryption.encrypt_message(message, public_pem)
decrypted = encryption.decrypt_message(encrypted, private_pem)

print(decrypted == message)  # Should be: True
```

---

## ✅ Phase 10: Steganography Verification

```python
import io
import wave
from app.steganography import AudioSteganography, SteganographyValidator

# Create test WAV file
wav_buffer = io.BytesIO()
with wave.open(wav_buffer, 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(44100)
    w.writeframes(b'\x00\x00' * 88200)  # 2 seconds

wav_data = wav_buffer.getvalue()

# Verify it's valid
print(SteganographyValidator.is_valid_wav_file(wav_data))  # True

# Embed message
message = b"Hidden message"
modified = AudioSteganography.encode_message_to_audio(wav_data, message)

# Extract message
extracted = AudioSteganography.decode_message_from_audio(modified)

print(extracted == message)  # Should be: True
```

---

## ✅ Phase 11: File Integrity Verification

```python
from app.cryptography import FileIntegrity

# Calculate hash
data = b"Test file content"
hash1 = FileIntegrity.calculate_file_hash(data)
hash2 = FileIntegrity.calculate_file_hash(data)

print(hash1 == hash2)  # True - same data produces same hash

# Verify integrity
is_valid = FileIntegrity.verify_file_integrity(data, hash1)
print(is_valid)  # True

# Corrupted file
modified_data = b"Modified content"
is_valid = FileIntegrity.verify_file_integrity(modified_data, hash1)
print(is_valid)  # False
```

---

## ✅ Phase 12: Documentation Review

- [ ] README.md - 361 lines ✓
- [ ] INSTALLATION.md - 294 lines ✓
- [ ] QUICKSTART.md - 256 lines ✓
- [ ] API_DOCUMENTATION.md - 461 lines ✓
- [ ] SECURITY.md - 670 lines ✓
- [ ] PROJECT_INDEX.md - 453 lines ✓
- [ ] COMPLETE_SUMMARY.md - 415 lines ✓
- [ ] FIXES_APPLIED.md - 326 lines ✓

Each document should:
- [ ] Be readable and well-formatted
- [ ] Contain no broken links
- [ ] Have clear examples
- [ ] Include troubleshooting tips

---

## ✅ Phase 13: Performance Testing

### Startup Time
- [ ] Record startup time from `python run.py` to "Running on..."
- [ ] Expected: < 5 seconds

### Request Time
- [ ] Measure login request time
```bash
time curl -X POST http://localhost:5000/auth/login \
  -d "username=alice&password=password123" \
  -L
```
- [ ] Expected: < 500ms

### Database Query Time
- [ ] Test with many messages
```python
>>> from app.models import Message
>>> import time
>>> start = time.time()
>>> messages = Message.query.limit(1000).all()
>>> print(f"{(time.time()-start)*1000:.2f}ms")
```
- [ ] Expected: < 100ms

---

## ✅ Phase 14: Code Quality Checks

- [ ] No syntax errors:
```bash
python -m py_compile app/*.py
```
- [ ] Expected: No output (all files valid)

- [ ] No import errors:
```bash
python -c "from app import create_app; app = create_app()"
```
- [ ] Expected: No errors

---

## ✅ Phase 15: Final Sanity Checks

### Essential Functions
- [ ] User can register ✓
- [ ] User can login ✓
- [ ] User can view profile ✓
- [ ] User can view dashboard ✓
- [ ] App can encrypt/decrypt ✓
- [ ] App can hide/extract messages ✓
- [ ] Audit logs track actions ✓
- [ ] Rate limiting blocks abuse ✓

### Critical Files
- [ ] app/__init__.py exists and valid ✓
- [ ] Database file created ✓
- [ ] All dependencies installed ✓
- [ ] All templates render ✓
- [ ] All routes registered ✓

### Security
- [ ] Passwords are hashed ✓
- [ ] Sessions are secure ✓
- [ ] CSRF protection active ✓
- [ ] Input validation working ✓
- [ ] Rate limiting active ✓

---

## ✅ Deployment Readiness

If all checks pass, the application is ready to:

### Development Deployment
- [ ] Run locally: `python run.py`
- [ ] Share with team via Git
- [ ] Deploy to dev server

### Production Deployment
- [ ] Set `FLASK_ENV=production` in `.env`
- [ ] Use strong `SECRET_KEY`
- [ ] Deploy to Heroku/Vercel/Docker
- [ ] Set up HTTPS/SSL
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up monitoring/logging

---

## ✅ Final Status

### All 15 Phases Complete?

| Phase | Status | Required |
|-------|--------|----------|
| 1. Installation | ✓ | Yes |
| 2. Validation | ✓ | Yes |
| 3. Testing | ✓ | Yes |
| 4. Startup | ✓ | Yes |
| 5. Web UI | ✓ | Yes |
| 6. API | ✓ | Yes |
| 7. Database | ✓ | Yes |
| 8. Security | ✓ | Yes |
| 9. Cryptography | ✓ | Yes |
| 10. Steganography | ✓ | Yes |
| 11. File Integrity | ✓ | Yes |
| 12. Documentation | ✓ | No |
| 13. Performance | ✓ | No |
| 14. Code Quality | ✓ | No |
| 15. Final Checks | ✓ | Yes |

**If all required phases (Yes) pass: ✅ READY FOR USE**

---

## Sign-Off

```
Project: AuraCrypt
Version: 1.0.0
Status: COMPLETE & VERIFIED
Date: 2024

[ ] Development verified
[ ] Testing completed
[ ] Documentation reviewed
[ ] Security confirmed
[ ] Ready for deployment

Signature: _________________
```

---

**For assistance, refer to INSTALLATION.md or README.md**

**To report issues, check SECURITY.md for security concerns**

**For API details, see API_DOCUMENTATION.md**
