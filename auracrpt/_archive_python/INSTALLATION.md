# AuraCrypt - Installation Guide

## System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- 500 MB free disk space

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd auracrpt
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

This creates:
- SQLite database (auracrpt.db)
- All required tables
- 3 test users (alice, bob, charlie)

### 3. Run Application

```bash
python run.py
```

Visit: **http://localhost:5000**

## Test Users

Login with any of these accounts (password: `password123`):

| Username | Email | Role | Purpose |
|----------|-------|------|---------|
| alice | alice@example.com | sender | Send encrypted messages |
| bob | bob@example.com | receiver | Receive and extract messages |
| charlie | charlie@example.com | user | General user access |

## Validation

Before running the app, validate all components:

```bash
python validate.py
```

Expected output:
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

## Project Structure

```
auracrpt/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models (7 tables)
│   ├── auth.py              # Authentication & RBAC
│   ├── cryptography.py      # RSA encryption
│   ├── steganography.py     # LSB audio steganography
│   ├── ids_middleware.py    # Rate limiting & IDS
│   ├── routes.py            # Flask routes & API (15+ endpoints)
│   ├── templates/           # HTML templates (8 files)
│   └── uploads/             # User file uploads
├── config.py                # Configuration
├── run.py                   # Entry point
├── init_db.py              # Database initialization
├── validate.py             # Component validation
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── [Documentation files]
```

## Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///auracrpt.db
MAX_CONTENT_LENGTH=52428800
```

### Configuration Profiles

Edit `config.py` to switch profiles:

```python
# Development (default)
app = create_app('development')  # Debug mode enabled

# Testing
app = create_app('testing')      # In-memory database

# Production
app = create_app('production')   # Debug disabled, security enhanced
```

## Common Tasks

### Create New User Programmatically

```python
from app import create_app
from app.auth import AuthenticationManager

app = create_app('development')
with app.app_context():
    user, error = AuthenticationManager.register_user(
        username='john',
        email='john@example.com',
        password='secure_password123',
        role='sender'
    )
    if user:
        print(f"User created: {user.username}")
```

### Run Database Shell

```bash
python run.py shell
>>> db.session.query(User).all()
>>> db.session.query(Message).count()
```

### Reset Database

```bash
rm auracrpt.db
python init_db.py
```

### View Audit Logs

```python
from app import create_app
from app.models import AuditLog

app = create_app('development')
with app.app_context():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    for log in logs:
        print(f"{log.created_at}: {log.action} - {log.status}")
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Address already in use"

The port 5000 is already taken. Use a different port:
```bash
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

Or modify `run.py`:
```python
PORT = os.environ.get('PORT', 5000)
app.run(port=int(PORT))
```

### Issue: Database locked error

Close other instances and remove `instance/` folder:
```bash
rm -rf instance/
python init_db.py
```

### Issue: File upload fails

Ensure `uploads/` folder has write permissions:
```bash
mkdir -p uploads
chmod 755 uploads
```

## Deployment

### To Vercel

```bash
# Create requirements-prod.txt
pip freeze > requirements-prod.txt

# Create vercel.json
{
  "builds": [{ "src": "run.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "run.py" }]
}
```

### To Heroku

```bash
# Create Procfile
web: python run.py

# Deploy
git push heroku main
```

### To Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## Security Checklist

For production deployment:

- [ ] Set `DEBUG = False` in config.py
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Use PostgreSQL instead of SQLite
- [ ] Store private keys securely (HSM/vault)
- [ ] Set up rate limiting
- [ ] Enable CORS properly
- [ ] Use environment variables for secrets
- [ ] Regular security audits
- [ ] Keep dependencies updated

## Performance

### Database Optimization

- Indexes created on: `username`, `email`, `created_at`, `ip_address`
- Message queries are optimized with proper joins

### Caching

- User sessions cached by Flask-Login
- Public keys cached during encryption

### Monitoring

- All actions logged to audit_logs table
- Rate limiting prevents DDoS
- IP blocking for suspicious activity

## Support & Documentation

- **API Docs:** See `API_DOCUMENTATION.md`
- **Security:** See `SECURITY.md`
- **Quick Start:** See `QUICKSTART.md`
- **Main Readme:** See `README.md`

## Next Steps

1. ✓ Install dependencies
2. ✓ Initialize database
3. ✓ Run validation
4. ✓ Start application
5. → Upload audio files
6. → Embed encrypted messages
7. → Extract and decrypt

Enjoy secure audio steganography! 🔐
