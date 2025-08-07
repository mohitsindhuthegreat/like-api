import json
import os
import random


def load_tokens(server_name):
    """Load tokens from custom Neon database with randomization for India tokens"""
    try:
        from .models import TokenRecord
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
                
                # Enhanced randomization for ALL servers to avoid API errors
                if len(token_list) > 0:
                    # Create random starting point to avoid always using same tokens
                    random_start = random.randint(0, len(token_list) - 1)
                    # Rearrange tokens starting from random position
                    token_list = token_list[random_start:] + token_list[:random_start]
                    # Additional shuffle for better distribution
                    random.shuffle(token_list)
                    print(f"🔀 {server_name.upper()} tokens randomized from position {random_start}/{len(token_list)} - avoiding repeated token usage")
                
                print(f"📊 Loaded {len(token_list)} tokens from custom Neon database for {server_name.upper()} server")
                return token_list
            else:
                print(f"⚠️ No tokens found in custom Neon database for {server_name.upper()} server")
                return []
    except Exception as e:
        print(f"❌ Database token loading error: {e}")
        print(f"⚠️ Falling back to JSON token files for {server_name.upper()}")
        
        # Fallback to JSON files with randomization
        try:
            json_file = f"tokens/{server_name.lower()}.json"
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    tokens_data = json.load(f)
                    if tokens_data and len(tokens_data) > 0:
                        # Apply randomization to JSON tokens too
                        random.shuffle(tokens_data)
                        print(f"🔀 {server_name.upper()} JSON tokens randomized - {len(tokens_data)} tokens loaded")
                        return tokens_data
            return []
        except Exception as fallback_error:
            print(f"❌ JSON fallback also failed: {fallback_error}")
            return []
