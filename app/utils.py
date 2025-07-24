import json
import os
import logging

logger = logging.getLogger(__name__)

def load_tokens(server_name):
    """
    Load tokens for a specific server from the tokens configuration
    
    Args:
        server_name (str): Name of the server (IND, BR, US, etc.)
    
    Returns:
        list: List of token dictionaries or None if failed
    """
    try:
        tokens_file = os.path.join("tokens", "tokens.json")
        
        if not os.path.exists(tokens_file):
            logger.error(f"Tokens file not found: {tokens_file}")
            return None
        
        with open(tokens_file, 'r', encoding='utf-8') as f:
            all_tokens = json.load(f)
        
        # Get tokens for the specific server
        server_tokens = all_tokens.get(server_name, [])
        
        if not server_tokens:
            logger.warning(f"No tokens found for server: {server_name}")
            return None
        
        logger.info(f"Loaded {len(server_tokens)} tokens for server: {server_name}")
        return server_tokens
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in tokens file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading tokens: {e}")
        return None

def get_server_url(server_name):
    """
    Get the appropriate API URL for a server
    
    Args:
        server_name (str): Name of the server
    
    Returns:
        str: API base URL for the server
    """
    server_urls = {
        "IND": "https://client.ind.freefiremobile.com",
        "BR": "https://client.us.freefiremobile.com",
        "US": "https://client.us.freefiremobile.com",
        "SAC": "https://client.us.freefiremobile.com",
        "NA": "https://client.us.freefiremobile.com",
        "DEFAULT": "https://clientbp.ggblueshark.com"
    }
    
    return server_urls.get(server_name, server_urls["DEFAULT"])

def validate_uid(uid):
    """
    Validate if UID is in correct format
    
    Args:
        uid (str): Player UID to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        uid_int = int(uid)
        # Free Fire UIDs are typically 10-12 digits
        return 1000000000 <= uid_int <= 999999999999
    except (ValueError, TypeError):
        return False
