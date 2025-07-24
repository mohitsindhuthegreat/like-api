import json
import requests
import hashlib
import time

def generate_guest_token(guest_uid, guest_password, server_name="PK"):
    """Generate authentication token from guest account credentials"""
    try:
        # This is a simplified token generator based on guest credentials
        # In real implementation, this would involve the Free Fire authentication API
        timestamp = int(time.time())
        
        # Create a mock JWT-like token for guest accounts
        # This should be replaced with actual Free Fire guest authentication
        token_data = {
            "guest_uid": guest_uid,
            "guest_password": guest_password,
            "server": server_name,
            "timestamp": timestamp,
            "type": "guest_auth"
        }
        
        # For now, return the guest credentials as the token
        # This needs to be replaced with proper Free Fire API authentication
        return f"guest_{guest_uid}_{guest_password[:16]}"
        
    except Exception as e:
        print(f"ERROR: Failed to generate guest token: {e}")
        return None

def authenticate_guest_account(guest_uid, guest_password, server_name="PK"):
    """Authenticate guest account with Free Fire servers"""
    try:
        # This function should implement the actual Free Fire guest authentication
        # For now, we'll return a mock response structure
        return {
            "authenticated": True,
            "token": generate_guest_token(guest_uid, guest_password, server_name),
            "account_id": guest_uid,
            "server": server_name
        }
    except Exception as e:
        print(f"ERROR: Guest authentication failed: {e}")
        return None

def validate_token_format(token):
    """Validate if token is in correct format"""
    try:
        if token.startswith("eyJ"):  # JWT token
            return "jwt"
        elif token.startswith("guest_"):  # Guest token
            return "guest"
        else:
            return "unknown"
    except:
        return "invalid"