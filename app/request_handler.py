import aiohttp
import asyncio
import requests
from app.utils import load_tokens
from app.encryption import encrypt_message
from app.protobuf_handler import create_like_protobuf, decode_protobuf


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
            "ReleaseVersion": "OB49",
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


async def send_multiple_requests(uid, server_name, url):
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

    # Send likes using ALL available tokens for maximum impact
    successful_requests = 0
    max_concurrent = min(15, len(tokens))  # Controlled concurrency for stability
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def send_with_semaphore(token):
        async with semaphore:
            result = await send_request(encrypted_uid, token, url, uid)
            if result is not None:
                return 1
            return 0
    
    # Use ALL available tokens for maximum like sending
    tasks = [send_with_semaphore(tokens[i]["token"]) for i in range(len(tokens))]
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
