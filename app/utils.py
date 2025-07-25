import json
import os


def load_tokens(server_name):
    """Load tokens from database first, fallback to file system"""
    try:
        # First try to load from database
        try:
            from models import TokenRecord
            from flask import current_app
            
            with current_app.app_context():
                tokens = TokenRecord.query.filter_by(server_name=server_name.upper()).all()
                if tokens:
                    token_list = []
                    for token_record in tokens:
                        token_list.append({
                            "token": token_record.token,
                            "uid": token_record.uid,
                            "server": server_name.upper()
                        })
                    print(f"📊 Loaded {len(token_list)} tokens from database for {server_name.upper()} server")
                    return token_list
        except Exception as db_error:
            print(f"⚠️ Database token loading failed: {db_error}")
        
        # Fallback to file system
        if server_name.upper() == "IND":
            path = "tokens/ind.json"
        elif server_name.upper() == "PK":
            path = "tokens/pk.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "tokens/br.json"
        elif server_name == "BD":
            path = "tokens/bd.json"
        elif server_name == "SG":
            path = "tokens/sg.json"
        else:
            path = "tokens/bd.json"
            
        if os.path.exists(path):
            with open(path, "r") as f:
                tokens = json.load(f)
                print(f"📄 Loaded {len(tokens)} tokens from file for {server_name.upper()} server")
                return tokens
        return None
    except Exception as e:
        print(f"❌ Error loading tokens: {e}")
        return None
