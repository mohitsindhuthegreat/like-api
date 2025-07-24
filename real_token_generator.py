import json
import time
import threading
import schedule
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import my_pb2
import output_pb2
import warnings
from urllib3.exceptions import InsecureRequestWarning
import concurrent.futures
from threading import Lock

# Disable SSL warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

class RealTokenGenerator:
    def __init__(self):
        self.is_running = False
        self.generation_thread = None
        self.tokens_lock = Lock()
        # Create persistent session for reuse
        self.session = requests.Session()
        self.session.verify = False
        # Configure session with connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,
            pool_maxsize=100,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def get_token(self, password: str, uid: str, retry_count: int = 2) -> Optional[Dict]:
        """Get initial access token with retry logic"""
        for attempt in range(retry_count + 1):
            try:
                url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
                headers = {
                    "Host": "100067.connect.garena.com",
                    "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "close"
                }
                data = {
                    "uid": uid,
                    "password": password,
                    "response_type": "token",
                    "client_type": "2",
                    "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
                    "client_id": "100067"
                }
                
                res = self.session.post(url, headers=headers, data=data, timeout=8)
                if res.status_code == 200:
                    token_json = res.json()
                    if "access_token" in token_json and "open_id" in token_json:
                        return token_json
                        
                # If failed and not last attempt, wait shorter before retry
                if attempt < retry_count:
                    time.sleep(0.5)
                    
            except Exception as e:
                if attempt < retry_count:
                    time.sleep(0.5)
                    continue
                    
        return None

    def encrypt_message(self, key: bytes, iv: bytes, plaintext: bytes) -> bytes:
        """Encrypt message using AES"""
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_message = pad(plaintext, AES.block_size)
        return cipher.encrypt(padded_message)

    def parse_response(self, content: str) -> Dict:
        """Parse response content"""
        response_dict = {}
        lines = content.split("\n")
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                response_dict[key.strip()] = value.strip().strip('"')
        return response_dict

    def decode_jwt_payload(self, token: str) -> Dict:
        """Decode JWT token payload to extract readable nickname"""
        try:
            import base64
            import json
            
            # Split JWT token (header.payload.signature)
            parts = token.split('.')
            if len(parts) != 3:
                return {}
                
            # Decode payload (base64url)
            payload = parts[1]
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            
            # Decode base64
            decoded_bytes = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded_bytes.decode('utf-8'))
            
            return payload_data
            
        except Exception:
            return {}

    def clean_nickname(self, nickname: str) -> str:
        """Clean and make nickname readable with comprehensive Unicode handling"""
        if not nickname:
            return "Player"
            
        import re
        import unicodedata
        
        try:
            # Try to normalize Unicode characters first
            normalized = unicodedata.normalize('NFKD', nickname)
            
            # Comprehensive Unicode character mapping for special characters
            unicode_map = {
                # Small caps letters
                '\u1d22': 'R',  # ᴿ
                '\u1d0f': 'O',  # ᴏ
                '\u0280': 'R',  # ʀ 
                '\u3164': '',   # ㅤ (invisible separator)
                '\u026a': 'I',  # ɪ
                '\ua731': 'S',  # ꜱ
                '\u029f': 'L',  # ʟ
                '\u1d20': 'T',  # ᴛ
                '\u1d07': 'E',  # ᴇ
                '\u0299': 'B',  # ʙ
                '\u029c': 'H',  # ʜ
                '\u0274': 'N',  # ɴ
                '\u1d04': 'C',  # ᴄ
                '\u1d05': 'D',  # ᴅ
                '\u1d0a': 'J',  # ᴊ
                '\u1d0b': 'K',  # ᴋ
                '\u1d0c': 'L',  # ʟ
                '\u1d0d': 'M',  # ᴍ
                '\u1d18': 'P',  # ᴘ
                '\u1d1b': 'T',  # ᴛ
                '\u1d1c': 'U',  # ᴜ
                '\u1d21': 'V',  # ᴠ
                '\u1d22': 'W',  # ᴡ
                '\u028f': 'Y',  # ʏ
                '\u1d22': 'Z',  # ᴢ
                
                # Cherokee characters (commonly used in gaming nicknames)
                '\u13A0': 'A',  # Ꭰ
                '\u13A1': 'E',  # Ꭱ (example from your nickname)
                '\u13A2': 'I',  # Ꭲ
                '\u13A3': 'O',  # Ꭳ
                '\u13A4': 'U',  # Ꭴ
                '\u13A5': 'V',  # Ꭵ
                '\u13A6': 'GA', # Ꭶ
                '\u13A7': 'KA', # Ꭷ
                '\u13A8': 'GE', # Ꭸ
                '\u13A9': 'GI', # Ꭹ
                '\u13AA': 'GO', # Ꭺ
                '\u13AB': 'GU', # Ꭻ
                '\u13AC': 'GV', # Ꭼ
                '\u13AD': 'HA', # Ꭽ
                '\u13AE': 'HE', # Ꭾ (example from your nickname)
                '\u13AF': 'HI', # Ꭿ
                '\u13B0': 'HO', # Ꮀ
                '\u13EB': 'YV', # Ꮟ (example from your nickname)
                
                # Extended Latin and special characters
                '\u00f8': 'o',  # ø (example from your nickname)
                '\u043d': 'n',  # н (Cyrillic n, example from your nickname)
                '\u2ca7': 'L',  # Ⲗ (Coptic letter)
                '\u0fd0': '',   # Tibetan mark (remove)
                
                # Mathematical and modifier letters
                '\u1d2c': 'A',  # ᴬ
                '\u1d2d': 'AE', # ᴭ
                '\u1d2e': 'B',  # ᴮ
                '\u1d2f': 'B',  # ᴯ
                '\u1d30': 'D',  # ᴰ
                '\u1d31': 'E',  # ᴱ
                '\u1d32': 'E',  # ᴲ
                '\u1d33': 'G',  # ᴳ
                '\u1d34': 'H',  # ᴴ
                '\u1d35': 'I',  # ᴵ
                '\u1d36': 'J',  # ᴶ
                '\u1d37': 'K',  # ᴷ
                '\u1d38': 'L',  # ᴸ
                '\u1d39': 'M',  # ᴹ
                '\u1d3a': 'N',  # ᴺ
                '\u1d3c': 'O',  # ᴼ
                '\u1d3d': 'OU', # ᴽ
                '\u1d3e': 'P',  # ᴾ
                '\u1d3f': 'R',  # ᴿ
                '\u1d40': 'T',  # ᵀ
                '\u1d41': 'U',  # ᵁ
                '\u1d42': 'W',  # ᵂ
            }
            
            # Replace Unicode characters with readable equivalents
            cleaned = nickname
            for unicode_char, replacement in unicode_map.items():
                cleaned = cleaned.replace(unicode_char, replacement)
            
            # Remove remaining invisible/control characters and special marks
            cleaned = re.sub(r'[\u3164\u200b\u200c\u200d\ufeff\u0300-\u036f\u1ab0-\u1aff\u1dc0-\u1dff]', '', cleaned)
            
            # Remove control characters and format characters
            cleaned = re.sub(r'[\u0000-\u001f\u007f-\u009f\u2000-\u200f\u2028-\u202f\u205f-\u206f]', '', cleaned)
            
            # Clean up multiple underscores and spaces
            cleaned = re.sub(r'[_\s]{2,}', '_', cleaned)
            cleaned = cleaned.strip('_').strip()
            
            # If result is too short, try different approaches
            if len(cleaned) < 2:
                # Try to extract any ASCII letters/numbers first
                ascii_only = re.sub(r'[^\x20-\x7E]', '', nickname)
                ascii_only = re.sub(r'[^\w\s\-_]', '', ascii_only).strip()
                
                if len(ascii_only) >= 2:
                    return ascii_only
                
                # Try transliteration of common Unicode blocks
                transliterated = ""
                for char in nickname:
                    char_code = ord(char)
                    # Cherokee block
                    if 0x13A0 <= char_code <= 0x13F5:
                        transliterated += "Ch"
                    # Cyrillic block  
                    elif 0x0400 <= char_code <= 0x04FF:
                        transliterated += "Cy"
                    # Greek block
                    elif 0x0370 <= char_code <= 0x03FF:
                        transliterated += "Gr"
                    # Arabic block
                    elif 0x0600 <= char_code <= 0x06FF:
                        transliterated += "Ar"
                    # Keep ASCII and basic Latin
                    elif 0x0020 <= char_code <= 0x007E:
                        transliterated += char
                    # Other characters become X
                    elif char.isalpha():
                        transliterated += "X"
                
                if len(transliterated) >= 2:
                    return transliterated[:15]  # Limit length
                else:
                    return "FirePlayer"
            
            # Limit final length to reasonable size
            return cleaned[:20] if len(cleaned) <= 20 else cleaned[:17] + "..."
            
        except Exception as e:
            # Enhanced fallback: try multiple approaches
            try:
                # First try: ASCII extraction
                ascii_fallback = re.sub(r'[^\x20-\x7E]', '', nickname)
                ascii_fallback = re.sub(r'[^\w\s\-_]', '', ascii_fallback).strip()
                
                if len(ascii_fallback) >= 2:
                    return ascii_fallback
                
                # Second try: character count approach
                if len(nickname) > 0:
                    char_count = sum(1 for c in nickname if c.isalpha() or c.isdigit())
                    if char_count >= 3:
                        return f"Player_{char_count}chars"
                
                return "FirePlayer"
            except:
                return "FirePlayer"

    def generate_real_jwt_token(self, uid: str, password: str) -> Optional[Dict]:
        """Generate real JWT token using the complete process"""
        try:
            # Step 1: Get access token with retry
            token_data = self.get_token(password, uid, retry_count=3)
            if not token_data:
                return None

            # Step 2: Create protobuf message with exact same data as your working version
            game_data = my_pb2.GameData()
            game_data.timestamp = "2024-12-05 18:15:32"
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.108.3"
            game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
            game_data.device_type = "Handheld"
            game_data.network_provider = "Verizon Wireless"
            game_data.connection_type = "WIFI"
            game_data.screen_width = 1280
            game_data.screen_height = 960
            game_data.dpi = "240"
            game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
            game_data.total_ram = 5951
            game_data.gpu_name = "Adreno (TM) 640"
            game_data.gpu_version = "OpenGL ES 3.0"
            game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
            game_data.ip_address = "172.190.111.97"
            game_data.language = "en"
            game_data.open_id = token_data['open_id']
            game_data.access_token = token_data['access_token']
            game_data.platform_type = 4
            game_data.device_form_factor = "Handheld"
            game_data.device_model = "Asus ASUS_I005DA"
            game_data.field_60 = 32968
            game_data.field_61 = 29815
            game_data.field_62 = 2479
            game_data.field_63 = 914
            game_data.field_64 = 31213
            game_data.field_65 = 32968
            game_data.field_66 = 31213
            game_data.field_67 = 32968
            game_data.field_70 = 4
            game_data.field_73 = 2
            game_data.library_path = "/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/lib/arm"
            game_data.field_76 = 1
            game_data.apk_info = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/base.apk"
            game_data.field_78 = 6
            game_data.field_79 = 1
            game_data.os_architecture = "32"
            game_data.build_number = "2019117877"
            game_data.field_85 = 1
            game_data.graphics_backend = "OpenGLES2"
            game_data.max_texture_units = 16383
            game_data.rendering_api = 4
            game_data.encoded_field_89 = "\u0017T\u0011\u0017\u0002\b\u000eUMQ\bEZ\u0003@ZK;Z\u0002\u000eV\ri[QVi\u0003\ro\t\u0007e"
            game_data.field_92 = 9204
            game_data.marketplace = "3rd_party"
            game_data.encryption_key = "KqsHT2B4It60T/65PGR5PXwFxQkVjGNi+IMCK3CFBCBfrNpSUA1dZnjaT3HcYchlIFFL1ZJOg0cnulKCPGD3C3h1eFQ="
            game_data.total_storage = 111107
            game_data.field_97 = 1
            game_data.field_98 = 1
            game_data.field_99 = "4"
            game_data.field_100 = "4"

            # Step 3: Serialize and encrypt
            serialized_data = game_data.SerializeToString()
            encrypted_data = self.encrypt_message(AES_KEY, AES_IV, serialized_data)
            edata = binascii.hexlify(encrypted_data).decode()

            # Step 4: Send request to generate JWT
            url = "https://loginbp.common.ggbluefox.com/MajorLogin"
            headers = {
                'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
                'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip",
                'Content-Type': "application/octet-stream",
                'Expect': "100-continue",
                'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1",
                'ReleaseVersion': "OB49"
            }

            # Try the request with retry logic using persistent session
            for attempt in range(2):  # Reduced attempts for speed
                try:
                    response = self.session.post(url, data=bytes.fromhex(edata), headers=headers, timeout=12)
                    if response.status_code == 200:
                        break
                    elif attempt < 1:  # Not last attempt
                        time.sleep(0.3)
                        continue
                except Exception as e:
                    if attempt < 1:  # Not last attempt
                        time.sleep(0.3)
                        continue
                    else:
                        raise e

            if response.status_code == 200:
                example_msg = output_pb2.Garena_420()
                try:
                    example_msg.ParseFromString(response.content)
                    response_dict = self.parse_response(str(example_msg))
                    
                    if response_dict.get("status") and response_dict.get("token"):
                        jwt_token = response_dict.get("token", "N/A")
                        
                        # Decode JWT to get nickname
                        payload = self.decode_jwt_payload(jwt_token)
                        raw_nickname = payload.get("nickname", "")
                        clean_nickname = self.clean_nickname(raw_nickname)
                        
                        return {
                            "token": jwt_token
                        }
                    else:
                        logger.warning(f"Invalid JWT response for UID {uid}")
                        return None
                        
                except Exception as e:
                    logger.error(f"Failed to parse JWT response for UID {uid}: {str(e)}")
                    return None
            else:
                logger.error(f"JWT request failed for UID {uid}: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error generating JWT token for UID {uid}: {str(e)}")
            return None

    def load_accounts(self, file_path: str) -> List[Dict]:
        """Load accounts from JSON file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                
                # Handle both array format and line-by-line format
                if content.startswith('['):
                    # Array format (IND_ACC.json)
                    return json.loads(content)
                else:
                    # Line-by-line format (PK_ACC.json)
                    accounts = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line:
                            try:
                                accounts.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                    return accounts
                    
        except Exception as e:
            logger.error(f"Error loading accounts from {file_path}: {str(e)}")
            return []

    def save_tokens(self, tokens: List[Dict], file_path: str) -> bool:
        """Save tokens to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(tokens, f, indent=2)
            logger.info(f"Saved {len(tokens)} tokens to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving tokens to {file_path}: {str(e)}")
            return False

    def process_single_account(self, account_data):
        """Process a single account for token generation"""
        account, i, total_accounts, region_name = account_data
        try:
            guest_info = account.get('guest_account_info', {})
            uid = guest_info.get('com.garena.msdk.guest_uid')
            password = guest_info.get('com.garena.msdk.guest_password')
            
            if not uid or not password:
                logger.warning(f"Invalid account data at position {i}")
                return None

            logger.info(f"Generating REAL JWT token for {region_name} account {i}/{total_accounts} (UID: {uid})")
            
            token_result = self.generate_real_jwt_token(uid, password)
            if token_result:
                logger.info(f"✓ Generated REAL JWT token for UID {uid}")
                return token_result
            else:
                logger.warning(f"✗ Failed to generate token for UID {uid}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing account {i} in {region_name}: {str(e)}")
            return None

    def generate_tokens_for_region_parallel(self, account_file: str, output_file: str, region_name: str) -> int:
        """Generate tokens for all accounts in a region using parallel processing"""
        logger.info(f"Starting FAST parallel REAL JWT token generation for {region_name} region...")
        
        accounts = self.load_accounts(account_file)
        if not accounts:
            logger.warning(f"No accounts found in {account_file}")
            return 0

        total_accounts = len(accounts)
        successful_tokens = []
        
        # Prepare account data for parallel processing
        account_data_list = [
            (account, i+1, total_accounts, region_name) 
            for i, account in enumerate(accounts)
        ]
        
        # Use ThreadPoolExecutor for parallel processing with optimized thread count
        max_workers = min(15, total_accounts)  # Increased to 15 concurrent requests for even faster speed
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_account = {
                executor.submit(self.process_single_account, account_data): account_data 
                for account_data in account_data_list
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_account):
                result = future.result()
                if result:
                    with self.tokens_lock:
                        successful_tokens.append(result)

        # Save successful tokens
        if successful_tokens:
            self.save_tokens(successful_tokens, output_file)
            logger.info(f"✅ {region_name} FAST JWT token generation completed: {len(successful_tokens)}/{total_accounts} successful")
        else:
            logger.warning(f"❌ No tokens generated for {region_name}")
            
        return len(successful_tokens)

    def generate_all_tokens(self):
        """Generate tokens for all regions"""
        logger.info("🚀 Starting automatic REAL JWT token generation for all regions...")
        
        regions = [
            ("IND_ACC.json", "tokens/ind.json", "India"),
            ("PK_ACC.json", "tokens/pk.json", "Pakistan")
        ]
        
        total_generated = 0
        
        for account_file, output_file, region_name in regions:
            try:
                count = self.generate_tokens_for_region_parallel(account_file, output_file, region_name)
                total_generated += count
            except Exception as e:
                logger.error(f"Failed to generate tokens for {region_name}: {str(e)}")
        
        logger.info(f"🎉 REAL JWT token generation cycle completed! Total tokens generated: {total_generated}")

    def start_scheduler(self):
        """Start the automatic token generation scheduler"""
        if self.is_running:
            logger.warning("Token generator is already running")
            return
            
        self.is_running = True
        
        # Schedule token generation every 4 hours
        schedule.every(4).hours.do(self.generate_all_tokens)
        
        # Generate tokens immediately on start
        threading.Thread(target=self.generate_all_tokens, daemon=True).start()
        
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        self.generation_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.generation_thread.start()
        
        logger.info("🔄 REAL JWT Token generator started - will regenerate tokens every 4 hours")

    def stop_scheduler(self):
        """Stop the automatic token generation scheduler"""
        self.is_running = False
        if self.generation_thread:
            self.generation_thread.join(timeout=5)
        logger.info("⏹️ Token generator stopped")

    def get_status(self) -> Dict:
        """Get current status of token generator"""
        return {
            "is_running": self.is_running,
            "next_run": str(schedule.next_run()) if schedule.jobs else None,
            "jobs_count": len(schedule.jobs)
        }

# Global token generator instance
real_token_generator = RealTokenGenerator()

def start_token_generation():
    """Start the token generation service"""
    real_token_generator.start_scheduler()

def stop_token_generation():
    """Stop the token generation service"""
    real_token_generator.stop_scheduler()

def get_generator_status():
    """Get token generator status"""
    return real_token_generator.get_status()

def generate_tokens_now():
    """Generate tokens now"""
    real_token_generator.generate_all_tokens()

if __name__ == "__main__":
    # For testing purposes
    real_token_generator.start_scheduler()
    
    try:
        # Keep the script running
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Shutting down token generator...")
        real_token_generator.stop_scheduler()