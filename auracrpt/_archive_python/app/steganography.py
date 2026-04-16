"""
AuraCrypt Steganography Module
Implements LSB (Least Significant Bit) steganography for WAV audio files
"""

import wave
import struct
import io


class AudioSteganography:
    """Handles LSB steganography for WAV audio files"""
    
    @staticmethod
    def encode_message_to_audio(audio_data, message):
        """
        Embed encrypted message into WAV audio using LSB steganography
        Args:
            audio_data: bytes of WAV file
            message: bytes of encrypted message to hide
        Returns: modified WAV file bytes with embedded message
        """
        # Convert audio_data to BytesIO for processing
        audio_stream = io.BytesIO(audio_data)
        
        try:
            with wave.open(audio_stream, 'rb') as wav_file:
                n_frames = wav_file.getnframes()
                framerate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                compression_type = wav_file.getcomptype()
                
                # Read all frames
                frames = wav_file.readframes(n_frames)
            
            # Convert frames to list of samples for manipulation
            samples = list(struct.unpack(f'<{n_frames * channels}h', frames))
            
            # Convert message to bits
            message_bits = ''.join(format(byte, '08b') for byte in message)
            message_length = len(message)
            
            # Check if audio has enough capacity
            max_capacity = (len(samples) // 8)  # bytes that can be hidden
            if message_length > max_capacity:
                raise ValueError(f"Message too large. Max capacity: {max_capacity} bytes")
            
            # Embed message length (first 4 bytes = 32 bits)
            length_bits = format(message_length, '032b')
            bit_index = 0
            
            # Embed length
            for i in range(4):
                for j in range(8):
                    samples[bit_index] = (samples[bit_index] & ~1) | int(length_bits[bit_index])
                    bit_index += 1
            
            # Embed message
            for bit in message_bits:
                samples[bit_index] = (samples[bit_index] & ~1) | int(bit)
                bit_index += 1
            
            # Convert samples back to bytes
            modified_frames = struct.pack(f'<{len(samples)}h', *samples)
            
            # Create new WAV file with embedded message
            output_stream = io.BytesIO()
            with wave.open(output_stream, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(framerate)
                if compression_type != 'NONE':
                    wav_file.setcomptype(compression_type, 'description')
                wav_file.writeframes(modified_frames)
            
            return output_stream.getvalue()
        
        except Exception as e:
            raise ValueError(f"Error encoding message to audio: {str(e)}")
    
    @staticmethod
    def decode_message_from_audio(audio_data):
        """
        Extract encrypted message from WAV audio using LSB steganography
        Args:
            audio_data: bytes of WAV file with embedded message
        Returns: extracted message as bytes
        """
        audio_stream = io.BytesIO(audio_data)
        
        try:
            with wave.open(audio_stream, 'rb') as wav_file:
                n_frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                frames = wav_file.readframes(n_frames)
            
            # Convert frames to list of samples
            samples = list(struct.unpack(f'<{n_frames * channels}h', frames))
            
            # Extract message length (first 4 bytes)
            length_bits = ''
            for i in range(32):
                length_bits += str(samples[i] & 1)
            
            message_length = int(length_bits, 2)
            
            if message_length == 0 or message_length > len(samples) // 8:
                raise ValueError("Invalid or corrupted message length")
            
            # Extract message bits
            message_bits = ''
            for i in range(32, 32 + (message_length * 8)):
                message_bits += str(samples[i] & 1)
            
            # Convert bits to bytes
            message = bytes(int(message_bits[i:i+8], 2) for i in range(0, len(message_bits), 8))
            
            return message
        
        except Exception as e:
            raise ValueError(f"Error decoding message from audio: {str(e)}")
    
    @staticmethod
    def get_audio_capacity(audio_data):
        """
        Calculate maximum message size that can be hidden in audio
        Args:
            audio_data: bytes of WAV file
        Returns: maximum message size in bytes
        """
        try:
            audio_stream = io.BytesIO(audio_data)
            with wave.open(audio_stream, 'rb') as wav_file:
                n_frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
            
            # Maximum capacity: total samples - 4 bytes for length header
            max_capacity = ((n_frames * channels) // 8) - 4
            return max(0, max_capacity)
        
        except Exception as e:
            raise ValueError(f"Error calculating audio capacity: {str(e)}")


class SteganographyValidator:
    """Validates steganography operations"""
    
    @staticmethod
    def is_valid_wav_file(file_data):
        """Check if file is a valid WAV file"""
        try:
            audio_stream = io.BytesIO(file_data)
            with wave.open(audio_stream, 'rb') as wav_file:
                wav_file.getnframes()
            return True
        except:
            return False
    
    @staticmethod
    def has_embedded_message(audio_data):
        """
        Check if audio file has an embedded message
        (Note: This is a heuristic - presence of non-zero LSBs)
        """
        try:
            audio_stream = io.BytesIO(audio_data)
            with wave.open(audio_stream, 'rb') as wav_file:
                n_frames = wav_file.getnframes()
                channels = wav_file.getnchannels()
                frames = wav_file.readframes(min(1000, n_frames))
            
            samples = struct.unpack(f'<{len(frames)//2}h', frames)
            lsb_sum = sum(sample & 1 for sample in samples)
            
            # If more than 30% of LSBs are set, likely contains message
            return (lsb_sum / len(samples)) > 0.3
        except:
            return False
