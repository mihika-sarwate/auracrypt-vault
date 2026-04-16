# AuraCrypt API Documentation

Complete reference for AuraCrypt REST API endpoints.

## Base URL
```
http://localhost:5000
```

## Authentication
Most endpoints require user authentication via Flask-Login session cookies. Authentication state is maintained across requests.

## Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `413` - Payload Too Large
- `429` - Rate Limit Exceeded
- `500` - Server Error

---

## Authentication Endpoints

### Register User
**Endpoint:** `POST /auth/register`

**Description:** Create a new user account

**Request Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Request Body:**
```
username=alice&email=alice@example.com&password=SecurePass123&confirm_password=SecurePass123&role=sender
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | Unique username (3-80 chars) |
| email | string | Yes | Valid email address |
| password | string | Yes | Minimum 8 characters |
| confirm_password | string | Yes | Must match password |
| role | string | Yes | 'user', 'sender', or 'receiver' |

**Response (Success):**
```
Status: 302 Redirect
Location: /auth/login
Flash: "Registration successful! Please log in."
```

**Response (Error):**
```
Status: 302 Redirect
Location: /auth/register
Flash: "Password must be at least 8 characters"
```

---

### Login User
**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and create session

**Request Body:**
```
username=alice&password=SecurePass123&remember=on
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes | Username |
| password | string | Yes | Password |
| remember | boolean | No | Remember for 7 days |

**Response (Success):**
```
Status: 302 Redirect
Location: /dashboard
Set-Cookie: session=...; Path=/; HttpOnly
```

**Response (Error):**
```
Status: 302 Redirect
Location: /auth/login
Flash: "Invalid username or password"
```

---

### Logout User
**Endpoint:** `GET /auth/logout`

**Description:** End user session

**Authentication:** Required

**Response:**
```
Status: 302 Redirect
Location: /auth/login
Flash: "You have been logged out"
```

---

## Message Endpoints

### Embed Message
**Endpoint:** `POST /api/embed-message`

**Description:** Encrypt and hide a message in audio file

**Authentication:** Required (Sender role)

**Request Headers:**
```
Content-Type: multipart/form-data
```

**Request Body:**
```
file: <WAV_FILE>
recipient_id: "12345678-1234-5678-1234-567812345678"
message: "This is my secret message"
title: "Important Communication"
description: "Confidential report"
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | file | Yes | WAV audio file (max 50MB) |
| recipient_id | string | Yes | User ID of recipient |
| message | string | Yes | Secret message (max 100KB) |
| title | string | Yes | Message title |
| description | string | No | Message description |

**Response (Success):**
```json
{
  "success": true,
  "message_id": "uuid-string",
  "message": "Message embedded successfully"
}
Status: 201 Created
```

**Response (Error):**
```json
{
  "error": "Only WAV files are supported"
}
Status: 400 Bad Request
```

**Possible Errors:**
- Missing file or message
- Invalid WAV file format
- Message too large for audio capacity
- Recipient not found
- File size exceeds limit
- Message content validation failure

---

### Extract Message
**Endpoint:** `POST /api/extract-message/<message_id>`

**Description:** Extract and decrypt hidden message from audio

**Authentication:** Required (Receiver role)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| message_id | string | Yes (URL) | ID of message to extract |

**Response (Success):**
```json
{
  "success": true,
  "message": "Decrypted message text here",
  "encrypted_hex": "a1b2c3d4e5f6..."
}
Status: 200 OK
```

**Response (Error):**
```json
{
  "error": "You do not have permission to extract this message"
}
Status: 403 Forbidden
```

**Possible Errors:**
- Message not found (404)
- No permission to access (403)
- File integrity check failed (400)
- Audio corruption detected (400)
- Decryption failure (500)

---

### Download Audio File
**Endpoint:** `GET /api/download-audio/<message_id>`

**Description:** Download audio file for a message

**Authentication:** Required

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| message_id | string | Yes (URL) | ID of message |

**Response (Success):**
```
Status: 200 OK
Content-Type: audio/wav
Content-Disposition: attachment; filename="audio.wav"
<WAV_FILE_BYTES>
```

**Response (Error):**
```json
{
  "error": "You do not have permission to download this file"
}
Status: 403 Forbidden
```

---

## Key Management Endpoints

### Get User's Public Key
**Endpoint:** `GET /api/users/<username>/public-key`

**Description:** Retrieve user's RSA public key for encryption

**Authentication:** Not required (public endpoint)

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| username | string | Yes (URL) | Target user's username |

**Response (Success):**
```json
{
  "username": "alice",
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBg...",
  "key_size": 2048
}
Status: 200 OK
```

**Response (Error):**
```json
{
  "error": "User not found"
}
Status: 404 Not Found
```

---

## Audit Log Endpoints

### Get Audit Logs
**Endpoint:** `GET /api/audit-logs`

**Description:** Retrieve audit logs for current user (last 50 entries)

**Authentication:** Required

**Response (Success):**
```json
[
  {
    "id": "uuid-string",
    "action": "message_embedded",
    "action_type": "embed",
    "status": "success",
    "created_at": "2024-01-15T10:30:00"
  },
  {
    "id": "uuid-string",
    "action": "user_login",
    "action_type": "login",
    "status": "success",
    "created_at": "2024-01-15T10:00:00"
  }
]
Status: 200 OK
```

---

## Web Routes (HTML Pages)

### Dashboard
**Route:** `GET /dashboard`

**Authentication:** Required

**Description:** User dashboard with message overview

---

### Profile
**Route:** `GET /profile`

**Authentication:** Required

**Description:** User profile and public key management

---

### Embed Message Page
**Route:** `GET /embed`

**Authentication:** Required (Sender role)

**Description:** Web form for embedding messages

---

### Extract Message Page
**Route:** `GET /extract`

**Authentication:** Required (Receiver role)

**Description:** Web interface for extracting messages

---

### View Message
**Route:** `GET /messages/<message_id>`

**Authentication:** Required

**Description:** View details of a specific message

---

## Error Handling

### Rate Limiting
When rate limit is exceeded:
```json
{
  "error": "Rate limit exceeded"
}
Status: 429 Too Many Requests
```

### IP Blocking
When IP is blocked:
```json
{
  "error": "Your IP address has been blocked"
}
Status: 403 Forbidden
```

### Validation Errors
```json
{
  "error": "Invalid input"
}
Status: 400 Bad Request
```

---

## Example Workflows

### Complete Message Embedding Workflow

1. **Sender gets recipient's public key:**
```bash
GET /api/users/bob/public-key
```

2. **Sender embeds message in WAV file:**
```bash
POST /api/embed-message
  - file: audio.wav
  - recipient_id: bob_user_id
  - message: "Secret message"
  - title: "Secret Communication"
```

3. **Sender downloads the modified audio:**
```bash
GET /api/download-audio/message_id
```

4. **Sender sends audio to recipient via email/messaging**

### Complete Message Extraction Workflow

1. **Receiver receives audio file**

2. **Receiver logs in and navigates to Extract page:**
```bash
GET /extract
```

3. **Receiver selects message and extracts:**
```bash
POST /api/extract-message/message_id
```

4. **System decrypts and displays message**

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Include Content-Type headers in requests**
3. **Validate file types before uploading**
4. **Check response status codes**
5. **Handle errors gracefully in client code**
6. **Don't log sensitive data**
7. **Use secure session cookies**
8. **Implement timeouts for long operations**

---

## Rate Limits

- Authentication endpoints: 20 requests/hour per IP
- Regular endpoints: 100 requests/hour per IP
- File uploads: 10 requests/hour per IP

---

## Version History

**v1.0** (2024-01-15)
- Initial release
- Complete encryption and steganography
- Web UI and API
- Audit logging
- Rate limiting and IDS
