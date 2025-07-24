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
                
                res = requests.post(url, headers=headers, data=data, timeout=15)
                if res.status_code == 200:
                    token_json = res.json()
                    if "access_token" in token_json and "open_id" in token_json:
                        return token_json
                        
                # If failed and not last attempt, wait before retry
                if attempt < retry_count:
                    time.sleep(2)
                    
            except Exception as e:
                if attempt < retry_count:
                    time.sleep(2)
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
        """Clean and make nickname readable"""
        if not nickname:
            return "Player"
            
        # Remove special Unicode characters and make readable
        import re
        
        # Replace common encoded characters with readable text
        cleaned = nickname.replace('CHÃ—FF~', 'FF_')
        cleaned = re.sub(r'[^\w\s\-_]', '', cleaned)  # Remove special chars
        cleaned = cleaned.strip()
        
        # If still empty or too short, use a default
        if len(cleaned) < 2:
            return "FreeFire_Player"
            
        return cleaned

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

            # Add session for better connection handling with retry
            session = requests.Session()
            session.verify = False
            
            # Try the request with retry logic
            for attempt in range(3):
                try:
                    response = session.post(url, data=bytes.fromhex(edata), headers=headers, timeout=25)
                    if response.status_code == 200:
                        break
                    elif attempt < 2:  # Not last attempt
                        time.sleep(1)
                        continue
                except Exception as e:
                    if attempt < 2:  # Not last attempt
                        time.sleep(1)
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

    def generate_tokens_for_region(self, account_file: str, output_file: str, region_name: str) -> int:
        """Generate tokens for all accounts in a region"""
        logger.info(f"Starting REAL JWT token generation for {region_name} region...")
        
        accounts = self.load_accounts(account_file)
        if not accounts:
            logger.warning(f"No accounts found in {account_file}")
            return 0

        successful_tokens = []
        total_accounts = len(accounts)
        
        for i, account in enumerate(accounts, 1):
            try:
                guest_info = account.get('guest_account_info', {})
                uid = guest_info.get('com.garena.msdk.guest_uid')
                password = guest_info.get('com.garena.msdk.guest_password')
                
                if not uid or not password:
                    logger.warning(f"Invalid account data in {account_file} at position {i}")
                    continue

                logger.info(f"Generating REAL JWT token for {region_name} account {i}/{total_accounts} (UID: {uid})")
                
                token_result = self.generate_real_jwt_token(uid, password)
                if token_result:
                    successful_tokens.append(token_result)
                    logger.info(f"✓ Generated REAL JWT token for UID {uid}")
                else:
                    logger.warning(f"✗ Failed to generate token for UID {uid}")
                
                # Reduced delay to improve speed while avoiding rate limits
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error processing account {i} in {region_name}: {str(e)}")
                continue

        # Save successful tokens
        if successful_tokens:
            self.save_tokens(successful_tokens, output_file)
            logger.info(f"✅ {region_name} REAL JWT token generation completed: {len(successful_tokens)}/{total_accounts} successful")
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
                count = self.generate_tokens_for_region(account_file, output_file, region_name)
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