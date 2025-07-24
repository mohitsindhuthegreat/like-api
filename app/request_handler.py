import requests
import aiohttp
import asyncio
import time
import logging
from app.protobuf_handler import protobuf_handler
from app.encryption import enc, generate_request_signature

logger = logging.getLogger(__name__)

# Request headers for Free Fire API
DEFAULT_HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 10; SM-G973F Build/QP1A.190711.020)',
    'Content-Type': 'application/x-protobuf',
    'Accept': 'application/x-protobuf',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

def make_request(encrypted_uid, server_name, token):
    """
    Make a synchronous request to get player information
    
    Args:
        encrypted_uid (str): Encrypted player UID
        server_name (str): Server name
        token (str): Authentication token
    
    Returns:
        PlayerInfo: Player information protobuf message or None if failed
    """
    try:
        # Determine the API endpoint
        if server_name == "IND":
            base_url = "https://client.ind.freefiremobile.com"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            base_url = "https://client.us.freefiremobile.com"
        else:
            base_url = "https://clientbp.ggblueshark.com"
        
        url = f"{base_url}/GetPlayerInfo"
        
        # Create protobuf request
        request_data = protobuf_handler.create_player_info_request(encrypted_uid, server_name)
        
        # Prepare headers with token
        headers = DEFAULT_HEADERS.copy()
        headers['Authorization'] = f'Bearer {token}'
        headers['X-Server'] = server_name
        
        # Add timestamp and signature
        timestamp = int(time.time())
        headers['X-Timestamp'] = str(timestamp)
        headers['X-Signature'] = generate_request_signature(encrypted_uid, timestamp)
        
        # Make the request
        response = requests.post(url, data=request_data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Parse the protobuf response
            player_info = protobuf_handler.parse_player_info_response(response.content)
            logger.info(f"Successfully retrieved player info for UID: {encrypted_uid[:10]}...")
            return player_info
        else:
            logger.error(f"Request failed with status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in make_request: {e}")
        return None

async def send_like_request(session, uid, server_name, url, token):
    """
    Send a single like request asynchronously
    
    Args:
        session (aiohttp.ClientSession): HTTP session
        uid (str): Target UID
        server_name (str): Server name
        url (str): API endpoint URL
        token (str): Authentication token
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        encrypted_uid = enc(uid)
        
        # Create protobuf request
        request_data = protobuf_handler.create_like_request(
            target_uid=encrypted_uid,
            sender_uid=encrypted_uid,  # Using same UID as sender
            server_name=server_name
        )
        
        # Prepare headers
        headers = DEFAULT_HEADERS.copy()
        headers['Authorization'] = f'Bearer {token}'
        headers['X-Server'] = server_name
        
        # Add timestamp and signature
        timestamp = int(time.time())
        headers['X-Timestamp'] = str(timestamp)
        headers['X-Signature'] = generate_request_signature(encrypted_uid, timestamp)
        
        # Send the request
        async with session.post(url, data=request_data, headers=headers) as response:
            if response.status == 200:
                logger.debug(f"Like request successful for UID: {uid}")
                return True
            else:
                logger.warning(f"Like request failed with status {response.status}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending like request: {e}")
        return False

async def send_multiple_requests(uid, server_name, url, num_requests=50):
    """
    Send multiple like requests asynchronously
    
    Args:
        uid (str): Target UID
        server_name (str): Server name
        url (str): API endpoint URL
        num_requests (int): Number of requests to send
    
    Returns:
        int: Number of successful requests
    """
    try:
        # Load tokens for the server
        from app.utils import load_tokens
        tokens = load_tokens(server_name)
        
        if not tokens:
            logger.error("No tokens available for requests")
            return 0
        
        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            # Create tasks for multiple requests
            for i in range(num_requests):
                # Rotate through available tokens
                token = tokens[i % len(tokens)]["token"]
                
                task = send_like_request(session, uid, server_name, url, token)
                tasks.append(task)
                
                # Add small delay between task creation to avoid overwhelming the server
                if i % 10 == 0:
                    await asyncio.sleep(0.1)
            
            # Execute all tasks concurrently
            logger.info(f"Sending {num_requests} like requests for UID: {uid}")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful requests
            successful = sum(1 for result in results if result is True)
            logger.info(f"Completed {successful}/{num_requests} like requests successfully")
            
            return successful
            
    except Exception as e:
        logger.error(f"Error in send_multiple_requests: {e}")
        return 0

async def get_player_profile(uid, server_name):
    """
    Get player profile information asynchronously
    
    Args:
        uid (str): Player UID
        server_name (str): Server name
    
    Returns:
        dict: Player profile data or None if failed
    """
    try:
        from app.utils import load_tokens
        tokens = load_tokens(server_name)
        
        if not tokens:
            return None
        
        token = tokens[0]["token"]
        encrypted_uid = enc(uid)
        
        # Use synchronous request for now (can be converted to async if needed)
        player_info = make_request(encrypted_uid, server_name, token)
        
        if player_info:
            return protobuf_handler.message_to_dict(player_info)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting player profile: {e}")
        return None
