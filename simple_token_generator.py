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

class SimpleTokenGenerator:
    def __init__(self):
        self.is_running = False
        self.generation_thread = None
        
    def get_token(self, password: str, uid: str) -> Optional[Dict]:
        """Generate token for a single account"""
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
            
            res = requests.post(url, headers=headers, data=data, timeout=10)
            if res.status_code != 200:
                logger.warning(f"Failed to get initial token for UID {uid}: HTTP {res.status_code}")
                return None
                
            token_json = res.json()
            if "access_token" in token_json and "open_id" in token_json:
                return {
                    "token": token_json["access_token"]
                }
            else:
                logger.warning(f"Invalid token response for UID {uid}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting token for UID {uid}: {str(e)}")
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
        logger.info(f"Starting token generation for {region_name} region...")
        
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

                logger.info(f"Generating token for {region_name} account {i}/{total_accounts} (UID: {uid})")
                
                token_result = self.get_token(password, uid)
                if token_result:
                    successful_tokens.append(token_result)
                    logger.info(f"✓ Generated token for UID {uid}")
                else:
                    logger.warning(f"✗ Failed to generate token for UID {uid}")
                
                # Small delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing account {i} in {region_name}: {str(e)}")
                continue

        # Save successful tokens
        if successful_tokens:
            self.save_tokens(successful_tokens, output_file)
            logger.info(f"✅ {region_name} token generation completed: {len(successful_tokens)}/{total_accounts} successful")
        else:
            logger.warning(f"❌ No tokens generated for {region_name}")
            
        return len(successful_tokens)

    def generate_all_tokens(self):
        """Generate tokens for all regions"""
        logger.info("🚀 Starting automatic token generation for all regions...")
        
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
        
        logger.info(f"🎉 Token generation cycle completed! Total tokens generated: {total_generated}")

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
        
        logger.info("🔄 Token generator started - will regenerate tokens every 4 hours")

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
simple_token_generator = SimpleTokenGenerator()

def start_token_generation():
    """Start the token generation service"""
    simple_token_generator.start_scheduler()

def stop_token_generation():
    """Stop the token generation service"""
    simple_token_generator.stop_scheduler()

def get_generator_status():
    """Get token generator status"""
    return simple_token_generator.get_status()

def generate_tokens_now():
    """Generate tokens now"""
    simple_token_generator.generate_all_tokens()

if __name__ == "__main__":
    # For testing purposes
    simple_token_generator.start_scheduler()
    
    try:
        # Keep the script running
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Shutting down token generator...")
        simple_token_generator.stop_scheduler()