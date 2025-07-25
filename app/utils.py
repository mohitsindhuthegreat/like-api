import json
import os
import random


def load_tokens(server_name):
    """Load tokens from custom Neon database with randomization for India tokens"""
    try:
        from models import TokenRecord
        from flask import current_app
        
        with current_app.app_context():
            tokens = TokenRecord.query.filter_by(server_name=server_name.upper(), is_active=True).all()
            if tokens:
                token_list = []
                for token_record in tokens:
                    token_list.append({
                        "token": token_record.token,
                        "uid": token_record.uid,
                        "server": server_name.upper()
                    })
                
                # Enhanced randomization for India tokens to avoid API errors
                if server_name.upper() == "IND" and len(token_list) > 0:
                    # Create random starting point to avoid always using same tokens
                    random_start = random.randint(0, len(token_list) - 1)
                    # Rearrange tokens starting from random position
                    token_list = token_list[random_start:] + token_list[:random_start]
                    # Additional shuffle for better distribution
                    random.shuffle(token_list)
                    print(f"🔀 India tokens randomized from position {random_start}/{len(token_list)} - avoiding repeated token usage")
                
                print(f"📊 Loaded {len(token_list)} tokens from custom Neon database for {server_name.upper()} server")
                return token_list
            else:
                print(f"⚠️ No tokens found in custom Neon database for {server_name.upper()} server")
                return []
    except Exception as e:
        print(f"❌ Database token loading error: {e}")
        return []
