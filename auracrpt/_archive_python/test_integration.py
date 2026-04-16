#!/usr/bin/env python
"""
Integration tests for AuraCrypt
Tests complete workflows end-to-end
"""

import unittest
import io
import wave
import json
from app import create_app, db
from app.models import User, Message, AuditLog, PublicKey
from app.auth import AuthenticationManager
from app.cryptography import MessageEncryption, FileIntegrity, RSAKeyManager
from app.steganography import AudioSteganography, SteganographyValidator


class AuraCryptTestCase(unittest.TestCase):
    """Base test case with setup/teardown"""
    
    def setUp(self):
        """Set up test app and database"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Tear down test database"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_wav(self, duration_seconds=1):
        """Create a test WAV file"""
        wav_buffer = io.BytesIO()
        framerate = 44100
        channels = 1
        sample_width = 2
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(framerate)
            # Write silence
            samples = b'\x00\x00' * (framerate * duration_seconds)
            wav_file.writeframes(samples)
        
        return wav_buffer.getvalue()


class TestAuthentication(AuraCryptTestCase):
    """Test authentication module"""
    
    def test_user_registration(self):
        """Test user registration"""
        user, error = AuthenticationManager.register_user(
            'testuser', 'test@example.com', 'password123', 'sender'
        )
        
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'sender')
    
    def test_duplicate_username(self):
        """Test duplicate username rejection"""
        AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'user'
        )
        
        user, error = AuthenticationManager.register_user(
            'alice', 'alice2@example.com', 'password123', 'user'
        )
        
        self.assertIsNone(user)
        self.assertIsNotNone(error)
    
    def test_user_authentication(self):
        """Test user login"""
        AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'sender'
        )
        
        user = AuthenticationManager.authenticate_user('alice', 'password123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'alice')
    
    def test_wrong_password(self):
        """Test wrong password rejection"""
        AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'sender'
        )
        
        user = AuthenticationManager.authenticate_user('alice', 'wrongpassword')
        self.assertIsNone(user)
    
    def test_public_key_generation(self):
        """Test RSA key generation for user"""
        user, _ = AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'sender'
        )
        
        public_key = AuthenticationManager.get_user_public_key(user.id)
        self.assertIsNotNone(public_key)
        self.assertTrue(public_key.public_key.startswith('-----BEGIN PUBLIC KEY-----'))


class TestCryptography(AuraCryptTestCase):
    """Test cryptography module"""
    
    def test_rsa_key_generation(self):
        """Test RSA keypair generation"""
        manager = RSAKeyManager(2048)
        private_key, public_key = manager.generate_keypair()
        
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
    
    def test_key_serialization(self):
        """Test PEM serialization"""
        manager = RSAKeyManager(2048)
        private_key, public_key = manager.generate_keypair()
        
        private_pem = manager.serialize_private_key(private_key)
        public_pem = manager.serialize_public_key(public_key)
        
        self.assertIn('-----BEGIN PRIVATE KEY-----', private_pem)
        self.assertIn('-----BEGIN PUBLIC KEY-----', public_pem)
    
    def test_message_encryption_decryption(self):
        """Test message encryption and decryption"""
        manager = RSAKeyManager(2048)
        private_key, public_key = manager.generate_keypair()
        
        public_pem = manager.serialize_public_key(public_key)
        private_pem = manager.serialize_private_key(private_key)
        
        encryption = MessageEncryption()
        original_message = "Secret message for testing"
        
        encrypted = encryption.encrypt_message(original_message, public_pem)
        decrypted = encryption.decrypt_message(encrypted, private_pem)
        
        self.assertEqual(decrypted, original_message)
    
    def test_hex_encoding(self):
        """Test hex encoding of encrypted messages"""
        manager = RSAKeyManager(2048)
        _, public_key = manager.generate_keypair()
        public_pem = manager.serialize_public_key(public_key)
        
        encryption = MessageEncryption()
        message = "Test message"
        
        hex_encrypted = encryption.encrypt_message_hex(message, public_pem)
        self.assertIsInstance(hex_encrypted, str)
        self.assertTrue(all(c in '0123456789abcdef' for c in hex_encrypted))
    
    def test_file_integrity(self):
        """Test file hash calculation"""
        file_data = b"Test file content"
        hash1 = FileIntegrity.calculate_file_hash(file_data)
        hash2 = FileIntegrity.calculate_file_hash(file_data)
        
        # Same file should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different file should produce different hash
        different_data = b"Different content"
        hash3 = FileIntegrity.calculate_file_hash(different_data)
        self.assertNotEqual(hash1, hash3)
    
    def test_file_integrity_verification(self):
        """Test file integrity verification"""
        file_data = b"Original file"
        hash_value = FileIntegrity.calculate_file_hash(file_data)
        
        # Verify correct file
        self.assertTrue(FileIntegrity.verify_file_integrity(file_data, hash_value))
        
        # Verify modified file
        modified_data = b"Modified file"
        self.assertFalse(FileIntegrity.verify_file_integrity(modified_data, hash_value))


class TestSteganography(AuraCryptTestCase):
    """Test audio steganography module"""
    
    def test_wav_validation(self):
        """Test WAV file validation"""
        wav_data = self.create_test_wav()
        
        self.assertTrue(SteganographyValidator.is_valid_wav_file(wav_data))
        self.assertFalse(SteganographyValidator.is_valid_wav_file(b'not a wav file'))
    
    def test_audio_capacity(self):
        """Test audio capacity calculation"""
        wav_data = self.create_test_wav(duration_seconds=1)
        capacity = AudioSteganography.get_audio_capacity(wav_data)
        
        # Should be able to hide at least some data
        self.assertGreater(capacity, 0)
    
    def test_message_embedding_and_extraction(self):
        """Test embedding and extracting messages"""
        wav_data = self.create_test_wav(duration_seconds=2)
        message = b"Secret message in audio!"
        
        # Embed message
        modified_audio = AudioSteganography.encode_message_to_audio(wav_data, message)
        
        # Extract message
        extracted = AudioSteganography.decode_message_from_audio(modified_audio)
        
        self.assertEqual(extracted, message)
    
    def test_large_message_rejection(self):
        """Test that oversized messages are rejected"""
        wav_data = self.create_test_wav(duration_seconds=1)
        large_message = b"x" * 100000  # Too large
        
        with self.assertRaises(ValueError):
            AudioSteganography.encode_message_to_audio(wav_data, large_message)
    
    def test_embedding_detection(self):
        """Test detection of embedded messages"""
        wav_data = self.create_test_wav()
        
        # Original file shouldn't appear to have message
        # (unless LSBs happen to be set)
        has_message_before = SteganographyValidator.has_embedded_message(wav_data)
        
        # Embed message
        message = b"Embedded message"
        modified_audio = AudioSteganography.encode_message_to_audio(wav_data, message)
        
        # Modified file should appear to have message
        has_message_after = SteganographyValidator.has_embedded_message(modified_audio)
        self.assertTrue(has_message_after)


class TestDatabase(AuraCryptTestCase):
    """Test database models"""
    
    def test_user_creation(self):
        """Test user model"""
        user = User(
            username='testuser',
            email='test@example.com',
            role='sender'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        retrieved_user = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(retrieved_user)
        self.assertTrue(retrieved_user.check_password('password123'))
    
    def test_message_creation(self):
        """Test message model"""
        sender, _ = AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'sender'
        )
        recipient, _ = AuthenticationManager.register_user(
            'bob', 'bob@example.com', 'password123', 'receiver'
        )
        
        message = Message(
            sender_id=sender.id,
            recipient_id=recipient.id,
            title='Test Message',
            description='A test message',
            audio_file_name='test.wav',
            audio_file_path='/tmp/test.wav',
            audio_file_size=1024,
            audio_file_hash='abc123',
            encrypted_message='encrypted_data',
            message_size=256,
            embedding_method='lsb'
        )
        
        db.session.add(message)
        db.session.commit()
        
        retrieved = Message.query.filter_by(title='Test Message').first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.sender_id, sender.id)
    
    def test_audit_logging(self):
        """Test audit log creation"""
        user, _ = AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'user'
        )
        
        logs = AuditLog.query.filter_by(user_id=user.id).all()
        self.assertGreater(len(logs), 0)


class TestEndToEnd(AuraCryptTestCase):
    """End-to-end workflow tests"""
    
    def test_complete_encryption_workflow(self):
        """Test complete encryption workflow"""
        # Create sender and receiver
        sender, _ = AuthenticationManager.register_user(
            'alice', 'alice@example.com', 'password123', 'sender'
        )
        recipient, _ = AuthenticationManager.register_user(
            'bob', 'bob@example.com', 'password123', 'receiver'
        )
        
        # Get encryption keys
        sender_key = AuthenticationManager.get_user_public_key(sender.id)
        recipient_key = AuthenticationManager.get_user_public_key(recipient.id)
        
        self.assertIsNotNone(sender_key)
        self.assertIsNotNone(recipient_key)
        
        # Prepare audio and message
        wav_data = self.create_test_wav(duration_seconds=2)
        message_text = "Secret message from Alice to Bob"
        
        # Encrypt message
        encryption = MessageEncryption()
        encrypted_message = encryption.encrypt_message(message_text, recipient_key.public_key)
        
        # Embed in audio
        modified_audio = AudioSteganography.encode_message_to_audio(
            wav_data, encrypted_message
        )
        
        # Verify integrity
        file_hash = FileIntegrity.calculate_file_hash(modified_audio)
        is_valid = FileIntegrity.verify_file_integrity(modified_audio, file_hash)
        self.assertTrue(is_valid)
        
        # Extract from audio (simulating receiver)
        extracted_encrypted = AudioSteganography.decode_message_from_audio(modified_audio)
        
        # Verify extracted data matches original encrypted data
        self.assertEqual(extracted_encrypted, encrypted_message)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()
