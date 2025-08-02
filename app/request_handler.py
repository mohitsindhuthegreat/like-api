import aiohttp
import asyncio
import requests
from utils import load_tokens
from encryption import encrypt_message
from protobuf_handler import create_like_protobuf, decode_protobuf


async def send_request(encrypted_uid, token, url, uid="", max_retries=3):
    try:
        edata = bytes.fromhex(encrypted_uid)
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB50",
        }
        
        # Enhanced retry logic for specific UIDs
        if uid == "2926998273":
            max_retries = 8  # More retries for problematic UID
            timeout = aiohttp.ClientTimeout(total=15)  # Longer timeout
        else:
            timeout = aiohttp.ClientTimeout(total=8)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for attempt in range(max_retries + 1):
                try:
                    async with session.post(url, data=edata, headers=headers) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 401:
                            # Token expired or invalid - don't retry
                            print(f"🔒 Token expired/invalid for UID {uid} (HTTP 401)")
                            return None
                        elif response.status == 403:
                            # Token forbidden - likely expired
                            print(f"🚫 Token forbidden for UID {uid} (HTTP 403)")
                            return None
                        elif response.status == 429:
                            # Rate limited - progressive backoff
                            if attempt < max_retries:
                                wait_time = (attempt + 1) * 2.0
                                await asyncio.sleep(wait_time)
                                continue
                        elif response.status >= 500:
                            # Server error - retry
                            if attempt < max_retries:
                                await asyncio.sleep(1.0 + attempt)
                                continue
                        else:
                            # Other errors - quick retry only
                            if attempt < 2:
                                await asyncio.sleep(0.5)
                                continue
                        
                        return None
                        
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    if attempt < max_retries:
                        await asyncio.sleep(1.0 + attempt)
                        continue
                    return None
                    
            return None
            
    except Exception as e:
        print(f"❌ Request error for UID {uid}: {e}")
        return None


async def send_multiple_requests(uid, server_name, url, token_count=None):
    import random
    region = server_name
    protobuf_message = create_like_protobuf(uid, region)
    if protobuf_message is None:
        return None
    encrypted_uid = encrypt_message(protobuf_message)
    if encrypted_uid is None:
        return None

    tokens = load_tokens(server_name)
    if tokens is None:
        return None

    # Smart rotation system to prevent account overuse
    if token_count is None:
        # Use smart rotation - different subset each time to prevent overuse
        import hashlib
        from datetime import datetime
        
        total_tokens = len(tokens)
        
        # Create truly random selection for perfect rotation every time
        import time
        current_time = int(time.time())  # Use current timestamp for true randomness
        seed_string = f"{uid}_{server_name}_{current_time}_{total_tokens}"
        seed = int(hashlib.md5(seed_string.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)
        
        # Optimized rotation for maximum efficiency and account protection
        if server_name == "IND":
            # For India: Use exactly 200 random tokens per request for better like delivery
            tokens_to_use = min(200, total_tokens)
        elif server_name == "PK":
            # For Pakistan: Use all available accounts for maximum success
            tokens_to_use = total_tokens
        else:
            # For other servers: Use 60-80% of available tokens
            tokens_to_use = min(150, int(total_tokens * 0.7))
        
        # Randomly select tokens for this request
        selected_tokens = random.sample(tokens, tokens_to_use)
        if server_name == "IND":
            print(f"🇮🇳 India rotation: Using exactly 200 random tokens out of {total_tokens} for maximum likes")
        elif server_name == "PK":
            print(f"🇵🇰 Pakistan rotation: Using ALL {total_tokens} accounts for maximum success rate")
        else:
            print(f"🌍 {server_name} rotation: Using {tokens_to_use} tokens out of {total_tokens} available")
        print(f"♻️ Perfect random selection ensures excellent token rotation")
    else:
        # Use specified number of random tokens for backward compatibility
        max_tokens_to_use = min(token_count, len(tokens))
        if len(tokens) > max_tokens_to_use:
            # Randomly select tokens for better distribution
            selected_tokens = random.sample(tokens, max_tokens_to_use)
        else:
            selected_tokens = tokens
        print(f"🎯 Using {len(selected_tokens)} random tokens out of {len(tokens)} available for UID {uid}")
    
    successful_requests = 0
    # Optimized concurrency for faster API response
    if server_name == "IND":
        max_concurrent = 25  # Higher concurrency for India's 200 tokens for faster response
    elif server_name == "PK":
        max_concurrent = 30  # Maximum concurrency for Pakistan's full token usage
    else:
        max_concurrent = 20  # Moderate for other servers
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def send_with_semaphore(token):
        async with semaphore:
            result = await send_request(encrypted_uid, token, url, uid)
            if result is not None:
                return 1
            else:
                # Token might be expired or invalid, skip it
                print(f"❌ Skipping expired/invalid token for UID {uid}")
                return 0
    
    # Use ALL selected tokens for maximum success rate
    tasks = [send_with_semaphore(selected_tokens[i]["token"]) for i in range(len(selected_tokens))]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful requests
    for result in results:
        if not isinstance(result, Exception) and result == 1:
            successful_requests += 1
    
    print(f"✅ Successfully sent {successful_requests} like requests for UID {uid}")
    return successful_requests


def make_request(encrypt, server_name, token):
    if server_name == "IND":
        url = "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name == "PK":
        url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        url = "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

    edata = bytes.fromhex(encrypt)
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Expect": "100-continue",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB49",
    }
    try:
        response = requests.post(url, data=edata, headers=headers, verify=False, timeout=15)
        
        if response.status_code != 200:
            print(f"Request failed with status {response.status_code} for server {server_name}")
            return None
            
        result = decode_protobuf(response.content)
        if result is None:
            print(f"Failed to decode protobuf response for server {server_name}")
            
        return result
        
    except Exception as e:
        print(f"Exception in make_request for server {server_name}: {str(e)}")
        return None
