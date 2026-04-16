"""
AuraCrypt Test Suite
Comprehensive tests for cryptography, steganography, and authentication modules
"""

import unittest
import os
import tempfile
from io import BytesIO
import wave

from app import create_app, db
from app.models import User, PublicKey, Message, AuditLog
from app.auth import AuthenticationManager, RoleBasedAccessControl
from app.cryptography import RSAKeyManager, MessageEncryption, FileIntegrity
from app.steganography import AudioSteganography, SteganographyValidator


class CryptographyTestCase(unittest.TestCase):
    """Test RSA cryptography functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.key_manager = RSAKeyManager(key_size=2048)
        self.encryption = MessageEncryption()
    
    def test_keypair_generation(self):
        """Test RSA keypair generation"""
        private_key, public_key = self.key_manager.generate_keypair()
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
    
    def test_key_serialization(self):
        """Test key serialization and deserialization"""
        private_key, public_key = self.key_manager.generate_keypair()
        
        # Serialize
        private_pem = self.key_manager.serialize_private_key(private_key)
        public_pem = self.key_manager.serialize_public_key(public_key)
        
        self.assertIn('BEGIN PRIVATE KEY', private_pem)
        self.assertIn('BEGIN PUBLIC KEY', public_pem)
        
        # Deserialize
        restored_private = self.key_manager.deserialize_private_key(private_pem)
        restored_public = self.key_manager.deserialize_public_key(public_pem)
        
        self.assertIsNotNone(restored_private)
        self.assertIsNotNone(restored_public)
    
    def test_message_encryption_decryption(self):
        """Test message encryption and decryption"""
        private_key, public_key = self.key_manager.generate_keypair()
        
        public_pem = self.key_manager.serialize_public_key(public_key)
        private_pem = self.key_manager.serialize_private_key(private_key)
        
        # Test message
        original_message = "This is a secret message!"
        
        # Encrypt
        encrypted = self.encryption.encrypt_message(original_message, public_pem)
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, original_message.encode())
        
        # Decrypt
        decrypted = self.encryption.decrypt_message(encrypted, private_pem)
        self.assertEqual(decrypted, original_message)
    
    def test_message_encryption_hex(self):
        """Test hex-based encryption"""
        private_key, public_key = self.key_manager.generate_keypair()
        
        public_pem = self.key_manager.serialize_public_key(public_key)
        private_pem = self.key_manager.serialize_private_key(private_key)
        
        message = "Test message for hex encoding"
        
        # Encrypt to hex
        encrypted_hex = self.encryption.encrypt_message_hex(message, public_pem)
        self.assertIsInstance(encrypted_hex, str)
        
        # Decrypt from hex
        decrypted = self.encryption.decrypt_message_hex(encrypted_hex, private_pem)
        self.assertEqual(decrypted, message)
    
    def test_file_integrity(self):
        """Test file integrity verification"""
        test_data = b"Test file content"
        
        # Calculate hash
        hash1 = FileIntegrity.calculate_file_hash(test_data)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 64)  # SHA-256 is 64 hex characters
        
        # Verify integrity
        is_valid = FileIntegrity.verify_file_integrity(test_data, hash1)
        self.assertTrue(is_valid)
        
        # Modified data should fail verification
        modified_data = b"Modified content"
        is_valid = FileIntegrity.verify_file_integrity(modified_data, hash1)
        self.assertFalse(is_valid)


class SteganographyTestCase(unittest.TestCase):
    """Test audio steganography functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a test WAV file
        self.sample_rate = 44100
        self.duration = 1  # 1 second
        self.audio_data = self.create_test_wav()
    
    def create_test_wav(self):
        """Create a test WAV file"""
        import struct
        
        # Create WAV header and data
        num_samples = self.sample_rate * self.duration
        audio_bytes = BytesIO()
        
        with wave.open(audio_bytes, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            
            # Generate simple sine wave
            import math
            frames = []
            for i in range(num_samples):
                sample = int(32767 * math.sin(2 * math.pi * 440 * i / self.sample_rate))
                frames.append(struct.pack('<h', sample))
            
            wav_file.writeframes(b''.join(frames))
        
        return audio_bytes.getvalue()
    
    def test_wav_validation(self):
        """Test WAV file validation"""
        self.assertTrue(SteganographyValidator.is_valid_wav_file(self.audio_data))
        self.assertFalse(SteganographyValidator.is_valid_wav_file(b'invalid data'))
    
    def test_message_embedding_extraction(self):
        """Test message embedding and extraction"""
        message = b"Secret message!"
        
        # Embed message
        modified_audio = AudioSteganography.encode_message_to_audio(self.audio_data, message)
        self.assertIsNotNone(modified_audio)
        self.assertTrue(SteganographyValidator.is_valid_wav_file(modified_audio))
        
        # Extract message
        extracted = AudioSteganography.decode_message_from_audio(modified_audio)
        self.assertEqual(extracted, message)
    
    def test_audio_capacity(self):
        """Test audio capacity calculation"""
        capacity = AudioSteganography.get_audio_capacity(self.audio_data)
        self.assertGreater(capacity, 0)
        
        # Test that small message fits
        small_message = b"x" * (capacity - 100)
        modified_audio = AudioSteganography.encode_message_to_audio(self.audio_data, small_message)
        self.assertIsNotNone(modified_audio)
    
    def test_message_too_large(self):
        """Test handling of oversized messages"""
        capacity = AudioSteganography.get_audio_capacity(self.audio_data)
        large_message = b"x" * (capacity + 1000)
        
        with self.assertRaises(ValueError):
            AudioSteganography.encode_message_to_audio(self.audio_data, large_message)


class AuthenticationTestCase(unittest.TestCase):
    """Test authentication and authorization"""
    
    def setUp(self):
        """Set up test app and database"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up test database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_user_registration(self):
        """Test user registration"""
        with self.app.app_context():
            user, error = AuthenticationManager.register_user(
                'testuser',
                'test@example.com',
                'password123'
            )
            
            self.assertIsNotNone(user)
            self.assertIsNone(error)
            self.assertEqual(user.username, 'testuser')
            self.assertEqual(user.email, 'test@example.com')
            self.assertTrue(user.check_password('password123'))
    
    def test_duplicate_registration(self):
        """Test duplicate registration prevention"""
        with self.app.app_context():
            user1, error1 = AuthenticationManager.register_user(
                'testuser',
                'test@example.com',
                'password123'
            )
            self.assertIsNotNone(user1)
            
            # Try to register with same username
            user2, error2 = AuthenticationManager.register_user(
                'testuser',
                'other@example.com',
                'password123'
            )
            self.assertIsNone(user2)
            self.assertIn('already exists', error2)
    
    def test_user_authentication(self):
        """Test user authentication"""
        with self.app.app_context():
            # Register user
            AuthenticationManager.register_user(
                'testuser',
                'test@example.com',
                'password123'
            )
            
            # Test successful login
            user = AuthenticationManager.authenticate_user('testuser', 'password123')
            self.assertIsNotNone(user)
            self.assertEqual(user.username, 'testuser')
            
            # Test failed login
            user = AuthenticationManager.authenticate_user('testuser', 'wrongpassword')
            self.assertIsNone(user)
    
    def test_role_based_access(self):
        """Test role-based access control"""
        with self.app.app_context():
            # Create sender user
            sender, _ = AuthenticationManager.register_user(
                'sender',
                'sender@example.com',
                'password123',
                'sender'
            )
            
            # Test permission checking
            has_embed = RoleBasedAccessControl.user_has_permission(sender, 'embed_message')
            has_extract = RoleBasedAccessControl.user_has_permission(sender, 'extract_message')
            
            self.assertTrue(has_embed)
            self.assertFalse(has_extract)


class FlaskIntegrationTestCase(unittest.TestCase):
    """Test Flask application integration"""
    
    def setUp(self):
        """Set up test app"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_login_redirect(self):
        """Test that unauthenticated access redirects to login"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login', response.location)
    
    def test_registration_page(self):
        """Test registration page loads"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Account', response.data)
    
    def test_login_page(self):
        """Test login page loads"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AuraCrypt', response.data)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
