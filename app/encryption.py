import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import logging

logger = logging.getLogger(__name__)

# Default encryption key and IV for Free Fire API (these would normally be extracted from the game)
DEFAULT_KEY = b'1234567890123456'  # 16 bytes key
DEFAULT_IV = b'1234567890123456'   # 16 bytes IV

def enc(uid):
    """
    Encrypt UID for Free Fire API requests
    
    Args:
        uid (str): Player UID to encrypt
    
    Returns:
        str: Base64 encoded encrypted UID
    """
    try:
        # Convert UID to bytes
        uid_bytes = uid.encode('utf-8')
        
        # Create AES cipher in CBC mode
        cipher = AES.new(DEFAULT_KEY, AES.MODE_CBC, DEFAULT_IV)
        
        # Pad the data to be multiple of 16 bytes
        padded_data = pad(uid_bytes, AES.block_size)
        
        # Encrypt the data
        encrypted_data = cipher.encrypt(padded_data)
        
        # Encode to base64 for transmission
        encoded_data = base64.b64encode(encrypted_data).decode('utf-8')
        
        logger.debug(f"Encrypted UID: {uid} -> {encoded_data[:20]}...")
        return encoded_data
        
    except Exception as e:
        logger.error(f"Encryption error: {e}")
        raise

def dec(encrypted_uid):
    """
    Decrypt encrypted UID
    
    Args:
        encrypted_uid (str): Base64 encoded encrypted UID
    
    Returns:
        str: Decrypted UID
    """
    try:
        # Decode from base64
        encrypted_data = base64.b64decode(encrypted_uid.encode('utf-8'))
        
        # Create AES cipher in CBC mode
        cipher = AES.new(DEFAULT_KEY, AES.MODE_CBC, DEFAULT_IV)
        
        # Decrypt the data
        decrypted_data = cipher.decrypt(encrypted_data)
        
        # Remove padding
        unpadded_data = unpad(decrypted_data, AES.block_size)
        
        # Convert back to string
        uid = unpadded_data.decode('utf-8')
        
        logger.debug(f"Decrypted UID: {encrypted_uid[:20]}... -> {uid}")
        return uid
        
    except Exception as e:
        logger.error(f"Decryption error: {e}")
        raise

def generate_request_signature(data, timestamp):
    """
    Generate request signature for API authentication
    
    Args:
        data (str): Request data
        timestamp (int): Request timestamp
    
    Returns:
        str: Generated signature
    """
    try:
        # This would implement the actual signature generation logic
        # For now, return a placeholder
        signature_data = f"{data}:{timestamp}".encode('utf-8')
        cipher = AES.new(DEFAULT_KEY, AES.MODE_CBC, DEFAULT_IV)
        padded_data = pad(signature_data, AES.block_size)
        encrypted_signature = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_signature).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Signature generation error: {e}")
        raise
