import aiohttp
import asyncio
import requests
from .utils import load_tokens
from .encryption import encrypt_message
from .protobuf_handler import create_like_protobuf, decode_protobuf


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
        
        # Enhanced retry logic with optimized timeouts for faster processing
        if uid == "2926998273":
            max_retries = 6  # Balanced retries for specific UID
            timeout = aiohttp.ClientTimeout(total=12)  # Optimized timeout
        else:
            timeout = aiohttp.ClientTimeout(total=6)  # Reduced timeout for faster processing
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for attempt in range(max_retries + 1):
                try:
                    async with session.post(url, data=edata, headers=headers) as response:
                        if response.status == 200:
                            return await response.text()
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

    # Enhanced like sending strategy for OB50 - Optimized for 6-hour cycles
    if server_name == "IND":
        # India: Use 250 random tokens for maximum likes (increased for 6-hour cycle)
        MAX_REQUESTS = min(len(tokens), 250)
        max_concurrent = min(12, len(tokens))  # Increased concurrency for faster processing
        print(f"🎯 India Strategy: Sending {MAX_REQUESTS} requests for UID {uid} using random token selection")
    elif server_name == "PK":
        # Pakistan: Use ALL available tokens for maximum success rate
        MAX_REQUESTS = len(tokens)
        max_concurrent = min(10, len(tokens))  # Increased concurrency for Pakistan
        print(f"🎯 Pakistan Strategy: Sending {MAX_REQUESTS} requests for UID {uid} using ALL tokens")
    else:
        # Other servers: Enhanced approach for faster processing
        MAX_REQUESTS = min(len(tokens), 200)
        max_concurrent = min(12, len(tokens))
        print(f"🎯 {server_name} Strategy: Sending {MAX_REQUESTS} requests for UID {uid}")
    
    successful_requests = 0
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def send_with_semaphore(token):
        async with semaphore:
            result = await send_request(encrypted_uid, token, url, uid)
            if result is not None:
                return 1
            return 0
    
    # OB50 optimized batch processing with smart delays - Enhanced for 6-hour cycle
    if server_name == "IND":
        batch_size = 75  # Larger batches for India - faster processing
        batch_delay = 0.3  # Reduced delay for faster throughput
    elif server_name == "PK": 
        batch_size = 50  # Increased batch size for Pakistan
        batch_delay = 0.7  # Optimized delay for Pakistan API stability
    else:
        batch_size = 60  # Increased batch size for faster processing
        batch_delay = 0.5  # Reduced delay for better performance
        
    total_sent = 0
    
    for batch_start in range(0, min(MAX_REQUESTS, len(tokens)), batch_size):
        batch_end = min(batch_start + batch_size, min(MAX_REQUESTS, len(tokens)))
        batch_tokens = tokens[batch_start:batch_end]
        
        print(f"📤 Sending batch {batch_start//batch_size + 1}: tokens {batch_start+1}-{batch_end}")
        
        tasks = [send_with_semaphore(token["token"]) for token in batch_tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful requests in this batch
        batch_success = 0
        for result in results:
            if not isinstance(result, Exception) and result == 1:
                batch_success += 1
        
        successful_requests += batch_success
        total_sent += len(batch_tokens)
        
        print(f"✅ Batch completed: {batch_success}/{len(batch_tokens)} successful, Total: {successful_requests}/{total_sent}")
        
        # Add delay between batches for OB50 API stability
        if batch_start + batch_size < min(MAX_REQUESTS, len(tokens)):
            await asyncio.sleep(batch_delay)
        
        # Continue until we've used all allocated tokens
        if total_sent >= MAX_REQUESTS:
            print(f"🎯 Completed all {MAX_REQUESTS} requests with {successful_requests} successful")
            break
    
    print(f"✅ Final result: {successful_requests} successful requests sent for UID {uid}")
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
        "ReleaseVersion": "OB50",
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
