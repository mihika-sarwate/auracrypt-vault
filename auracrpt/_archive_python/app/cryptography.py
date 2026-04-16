"""
AuraCrypt Cryptography Module
Implements RSA 2048-bit encryption for secure message protection
"""

import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend


class RSAKeyManager:
    """Manages RSA key generation, storage, and retrieval"""
    
    def __init__(self, key_size=2048):
        self.key_size = key_size
        self.backend = default_backend()
    
    def generate_keypair(self):
        """
        Generate RSA keypair (2048-bit)
        Returns: (private_key, public_key)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.key_size,
            backend=self.backend
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    def serialize_private_key(self, private_key):
        """Serialize private key to PEM format"""
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode('utf-8')
    
    def serialize_public_key(self, public_key):
        """Serialize public key to PEM format"""
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def deserialize_private_key(self, pem_data):
        """Deserialize private key from PEM format"""
        pem_bytes = pem_data.encode('utf-8') if isinstance(pem_data, str) else pem_data
        private_key = serialization.load_pem_private_key(
            pem_bytes,
            password=None,
            backend=self.backend
        )
        return private_key
    
    def deserialize_public_key(self, pem_data):
        """Deserialize public key from PEM format"""
        pem_bytes = pem_data.encode('utf-8') if isinstance(pem_data, str) else pem_data
        public_key = serialization.load_pem_public_key(
            pem_bytes,
            backend=self.backend
        )
        return public_key


class MessageEncryption:
    """Handles message encryption and decryption"""
    
    def __init__(self):
        self.key_manager = RSAKeyManager()
    
    def encrypt_message(self, message, public_key_pem):
        """
        Encrypt message using RSA public key
        Args:
            message: str or bytes to encrypt
            public_key_pem: PEM-formatted public key string
        Returns: encrypted bytes
        """
        if isinstance(message, str):
            message = message.encode('utf-8')
        
        public_key = self.key_manager.deserialize_public_key(public_key_pem)
        
        ciphertext = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext
    
    def decrypt_message(self, ciphertext, private_key_pem):
        """
        Decrypt message using RSA private key
        Args:
            ciphertext: encrypted bytes
            private_key_pem: PEM-formatted private key string
        Returns: decrypted message as string
        """
        private_key = self.key_manager.deserialize_private_key(private_key_pem)
        
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')
    
    def encrypt_message_hex(self, message, public_key_pem):
        """Encrypt message and return as hex string for easy storage"""
        ciphertext = self.encrypt_message(message, public_key_pem)
        return ciphertext.hex()
    
    def decrypt_message_hex(self, ciphertext_hex, private_key_pem):
        """Decrypt message from hex string"""
        ciphertext = bytes.fromhex(ciphertext_hex)
        return self.decrypt_message(ciphertext, private_key_pem)


class FileIntegrity:
    """Handles file integrity verification using SHA-256"""
    
    @staticmethod
    def calculate_file_hash(file_data):
        """
        Calculate SHA-256 hash of file
        Args:
            file_data: bytes or file path
        Returns: hex string of hash
        """
        if isinstance(file_data, str):
            # If string, treat as file path
            with open(file_data, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        else:
            # If bytes, calculate directly
            return hashlib.sha256(file_data).hexdigest()
    
    @staticmethod
    def verify_file_integrity(file_data, stored_hash):
        """
        Verify file integrity by comparing hashes
        Args:
            file_data: bytes or file path
            stored_hash: previously calculated hash
        Returns: True if hashes match, False otherwise
        """
        calculated_hash = FileIntegrity.calculate_file_hash(file_data)
        return calculated_hash == stored_hash
