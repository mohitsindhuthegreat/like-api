import json
import os


def load_tokens(server_name):
    """Load tokens from custom Neon database only - no file fallback"""
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
                print(f"📊 Loaded {len(token_list)} tokens from custom Neon database for {server_name.upper()} server")
                return token_list
            else:
                print(f"⚠️ No tokens found in custom Neon database for {server_name.upper()} server")
                return []
    except Exception as e:
        print(f"❌ Database token loading error: {e}")
        return []
