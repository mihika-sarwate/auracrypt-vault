#!/usr/bin/env python
"""
Comprehensive validation script to test all components
"""

import sys
import os

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        print("  ✓ Flask")
        import flask_sqlalchemy
        print("  ✓ Flask-SQLAlchemy")
        import flask_login
        print("  ✓ Flask-Login")
        from cryptography.hazmat.primitives.asymmetric import rsa
        print("  ✓ cryptography")
        import wave
        print("  ✓ wave")
        print("All dependencies imported successfully!\n")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}\n")
        return False

def test_app_creation():
    """Test Flask app creation"""
    print("Testing Flask app creation...")
    try:
        from app import create_app
        app = create_app('development')
        print("  ✓ Flask app created successfully")
        print(f"  ✓ Debug mode: {app.debug}")
        print(f"  ✓ Database: {app.config['SQLALCHEMY_DATABASE_URI']}\n")
        return True
    except Exception as e:
        print(f"  ✗ App creation failed: {e}\n")
        return False

def test_database():
    """Test database models and creation"""
    print("Testing database models...")
    try:
        from app import create_app, db
        from app.models import User, Message, PublicKey, AuditLog
        
        app = create_app('development')
        
        with app.app_context():
            # Check tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = ['users', 'public_keys', 'messages', 'audit_logs', 'ip_blocklist', 'rate_limit_tracker']
            for table in expected_tables:
                if table in tables:
                    print(f"  ✓ {table} table exists")
                else:
                    print(f"  ✗ {table} table missing")
                    return False
        
        print("All database tables verified!\n")
        return True
    except Exception as e:
        print(f"  ✗ Database test failed: {e}\n")
        return False

def test_cryptography():
    """Test RSA encryption"""
    print("Testing cryptography module...")
    try:
        from app.cryptography import RSAKeyManager, MessageEncryption
        
        # Generate keypair
        key_manager = RSAKeyManager(2048)
        private_key, public_key = key_manager.generate_keypair()
        print("  ✓ RSA keypair generated")
        
        # Serialize keys
        private_pem = key_manager.serialize_private_key(private_key)
        public_pem = key_manager.serialize_public_key(public_key)
        print("  ✓ Keys serialized to PEM")
        
        # Test encryption/decryption
        encryption = MessageEncryption()
        message = "Test message for encryption"
        encrypted = encryption.encrypt_message(message, public_pem)
        decrypted = encryption.decrypt_message(encrypted, private_pem)
        
        if decrypted == message:
            print("  ✓ Encryption/Decryption successful")
        else:
            print("  ✗ Encryption/Decryption mismatch")
            return False
        
        print("Cryptography tests passed!\n")
        return True
    except Exception as e:
        print(f"  ✗ Cryptography test failed: {e}\n")
        return False

def test_authentication():
    """Test authentication system"""
    print("Testing authentication...")
    try:
        from app import create_app, db
        from app.auth import AuthenticationManager
        
        app = create_app('development')
        
        with app.app_context():
            # Register user
            user, error = AuthenticationManager.register_user(
                'testuser', 'test@example.com', 'password123', 'user'
            )
            
            if user:
                print("  ✓ User registration successful")
            else:
                print(f"  ✗ User registration failed: {error}")
                return False
            
            # Authenticate user
            authenticated_user = AuthenticationManager.authenticate_user('testuser', 'password123')
            if authenticated_user:
                print("  ✓ User authentication successful")
            else:
                print("  ✗ User authentication failed")
                return False
            
            # Get public key
            public_key = AuthenticationManager.get_user_public_key(user.id)
            if public_key:
                print("  ✓ Public key retrieval successful")
            else:
                print("  ✗ Public key retrieval failed")
                return False
        
        print("Authentication tests passed!\n")
        return True
    except Exception as e:
        print(f"  ✗ Authentication test failed: {e}\n")
        return False

def test_steganography():
    """Test audio steganography"""
    print("Testing steganography module...")
    try:
        import io
        import wave
        from app.steganography import AudioSteganography, SteganographyValidator
        
        # Create a simple test WAV file
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            # Write 1 second of silence
            wav_file.writeframes(b'\x00\x00' * 44100)
        
        wav_data = wav_buffer.getvalue()
        
        # Validate WAV file
        if SteganographyValidator.is_valid_wav_file(wav_data):
            print("  ✓ WAV file validation successful")
        else:
            print("  ✗ WAV file validation failed")
            return False
        
        # Check capacity
        capacity = AudioSteganography.get_audio_capacity(wav_data)
        print(f"  ✓ Audio capacity calculated: {capacity} bytes")
        
        # Embed message
        test_message = b"Hello, World!"
        modified_audio = AudioSteganography.encode_message_to_audio(wav_data, test_message)
        print("  ✓ Message embedded in audio")
        
        # Extract message
        extracted = AudioSteganography.decode_message_from_audio(modified_audio)
        if extracted == test_message:
            print("  ✓ Message extraction successful")
        else:
            print("  ✗ Message extraction mismatch")
            return False
        
        print("Steganography tests passed!\n")
        return True
    except Exception as e:
        print(f"  ✗ Steganography test failed: {e}\n")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("AuraCrypt Validation Suite")
    print("=" * 60 + "\n")
    
    tests = [
        ("Dependencies", test_imports),
        ("Flask App", test_app_creation),
        ("Database", test_database),
        ("Cryptography", test_cryptography),
        ("Authentication", test_authentication),
        ("Steganography", test_steganography),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Unexpected error in {test_name}: {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AuraCrypt is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
