# AuraCrypt Quick Start Guide

Get AuraCrypt up and running in 5 minutes!

## Prerequisites
- Python 3.8+
- pip package manager

## Step 1: Install Dependencies (30 seconds)

```bash
cd auracrpt
pip install -r requirements.txt
```

## Step 2: Initialize Database (10 seconds)

```bash
python run.py
# Or manually:
# python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

This creates `auracrpt.db` with all necessary tables.

## Step 3: Start the Application (10 seconds)

```bash
python run.py
```

You should see:
```
* Running on http://0.0.0.0:5000
* Press CTRL+C to quit
```

## Step 4: Access the Web Interface

Open your browser and go to:
```
http://localhost:5000
```

You'll be redirected to the login page.

## Step 5: Create Your First Account

Click "Register" and fill in:
- **Username:** alice
- **Email:** alice@example.com
- **Password:** password123
- **Role:** Sender
- Click "Create Account"

## Step 6: Login

Use your new credentials to login.

## Step 7: Try Embedding a Message

1. Go to "Embed Message" (top navigation)
2. To test, you'll need another user. Open a new incognito window and:
   - Register another user as "Receiver"
   - Get their user ID from their profile page
3. Back in the first window:
   - Create or download a sample WAV file
   - Select the recipient
   - Write your secret message
   - Click "Embed & Encrypt Message"

## Step 8: Extract the Message

1. Switch to the receiver's account
2. Go to "Extract Message"
3. Click the message you received
4. Click "Extract & Decrypt"
5. View your secret message!

## Test Data Setup

To quickly set up test users, run:

```bash
flask seed-db
```

This creates three test users:
- **alice** (alice@example.com, sender)
- **bob** (bob@example.com, receiver)  
- **charlie** (charlie@example.com, user)

All with password: `password123`

## Common Tasks

### Reset Database

```bash
python -c "
from app import create_app, db
app = create_app()
app.app_context().push()
db.drop_all()
db.create_all()
print('Database reset!')
"
```

### Generate Test WAV Files

Python script to create test audio:

```python
import wave
import struct
import math

# Create a simple test WAV file
with wave.open('test_audio.wav', 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(44100)
    
    # Generate 3 seconds of 440Hz sine wave
    num_samples = 44100 * 3
    frames = []
    for i in range(num_samples):
        sample = int(32767 * math.sin(2 * math.pi * 440 * i / 44100))
        frames.append(struct.pack('<h', sample))
    
    wav.writeframes(b''.join(frames))

print("Created test_audio.wav")
```

### View Database Content

```bash
python -c "
from app import create_app
from app.models import User, Message, AuditLog

app = create_app()
app.app_context().push()

print('=== USERS ===')
for user in User.query.all():
    print(f'{user.username} - {user.role}')

print('\n=== MESSAGES ===')
for msg in Message.query.all():
    print(f'{msg.title} - {msg.sender.username} → {msg.recipient.username}')

print('\n=== AUDIT LOG (Last 10) ===')
for log in AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10):
    print(f'[{log.created_at}] {log.action} - {log.status}')
"
```

## Troubleshooting

### Port Already in Use

Change the port:
```bash
# In run.py, change the port parameter:
app.run(host='0.0.0.0', port=8000)
```

### Database Locked Error

Delete the database and reinitialize:
```bash
rm auracrpt.db
python run.py
```

### WAV File Issues

- Ensure file is valid WAV format
- Check file size (max 50MB)
- Use PCM audio (most common)
- Try mono files for better capacity

### Module Not Found

Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

### Permission Denied on macOS/Linux

```bash
chmod +x run.py
./run.py
```

## Project Structure Reference

```
auracrpt/
├── app/                      # Flask application
│   ├── cryptography.py       # RSA encryption
│   ├── steganography.py      # Audio hiding
│   ├── auth.py              # Authentication
│   ├── models.py            # Database models
│   ├── routes.py            # Web routes
│   └── templates/           # HTML pages
├── config.py                # Settings
├── run.py                   # Start here!
├── requirements.txt         # Dependencies
└── auracrpt.db             # Database (auto-created)
```

## Features to Explore

1. **Embed Message** - Hide text in audio using encryption
2. **Extract Message** - Decrypt and reveal hidden messages
3. **Profile** - View your RSA public key
4. **Audit Logs** - See all your account activity
5. **Role Management** - Different permissions for users

## Security Notes

⚠️ **This is a demonstration/educational system.**

For production use:
- Use HTTPS (not HTTP)
- Change the SECRET_KEY in config.py
- Use a proper database (PostgreSQL, MySQL)
- Deploy with Gunicorn/uWSGI
- Enable firewalls and security groups
- Implement backups
- Use environment variables for secrets

## Next Steps

1. **Explore the codebase** - Check out `app/cryptography.py` and `app/steganography.py`
2. **Run tests** - `python tests.py`
3. **Read documentation** - See `README.md` and `API_DOCUMENTATION.md`
4. **Customize** - Modify templates in `app/templates/`
5. **Deploy** - Follow production deployment guide in README.md

## Getting Help

- Check `README.md` for detailed documentation
- Review `API_DOCUMENTATION.md` for endpoint details
- Look at `tests.py` for code examples
- Check `config.py` for configuration options

---

Enjoy using AuraCrypt! 🔒
