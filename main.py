from flask import Flask, request, Response, render_template_string
import asyncio
import json
import os
from datetime import datetime
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
from real_token_generator import real_token_generator, start_token_generation, stop_token_generation, get_generator_status, generate_tokens_now
try:
    from models import db, PlayerRecord
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database models not available: {e}")
    DATABASE_AVAILABLE = False
from nickname_processor import nickname_processor

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure Flask to properly handle Unicode in JSON responses - ENHANCED
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
try:
    app.json.ensure_ascii = False
    app.json.sort_keys = False
except AttributeError:
    # Fallback for older Flask versions
    pass

# Custom JSON encoder to ensure proper Unicode display
import json
from flask.json.provider import DefaultJSONProvider

class UnicodeJSONProvider(DefaultJSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault('ensure_ascii', False)
        kwargs.setdefault('separators', (',', ':'))
        return json.dumps(obj, **kwargs)

app.json = UnicodeJSONProvider(app)

# Custom jsonify function for proper Unicode display
def unicode_jsonify(data, status_code=200):
    """Custom jsonify that properly handles Unicode characters"""
    response_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    response = Response(
        response_data,
        status=status_code,
        mimetype='application/json; charset=utf-8'
    )
    return response

# DISABLE EXTERNAL DATABASE - Keep everything internal
DATABASE_AVAILABLE = False
database_url = None
print("✅ Internal bot storage only - no external database")

# Internal storage for player records - NO EXTERNAL DATABASE
player_records = {}

def save_player_record(uid, nickname, server_name, likes_count):
    """Save player record internally in bot"""
    try:
        player_records[f"{uid}_{server_name}"] = {
            "uid": uid,
            "nickname": nickname,
            "server_name": server_name,
            "likes_count": likes_count,
            "last_updated": datetime.utcnow().isoformat()
        }
        app.logger.info(f"📝 Internal storage: UID {uid}: {nickname}")
        return True
    except Exception as e:
        app.logger.error(f"❌ Internal storage error for UID {uid}: {e}")
        return False


@app.route("/records", methods=["GET"])
def get_records():
    """Get all player records from internal storage"""
    try:
        records_list = list(player_records.values())
        # Sort by last_updated descending
        records_list.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
        return unicode_jsonify({
            "total_records": len(records_list),
            "records": records_list[:100],  # Limit to 100 recent records
            "message": "Internal bot storage"
        })
    except Exception as e:
        return unicode_jsonify({"error": str(e)}, 500)

import asyncio
from concurrent.futures import ThreadPoolExecutor

@app.route("/like", methods=["GET"])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    
    # Allow auto-detection if server_name is not provided
    if not uid:
        return unicode_jsonify({"error": "UID is required"}, 400)
    
    # If no server specified, try to auto-detect the correct server
    if not server_name:
        app.logger.info(f"Auto-detecting server for UID {uid}")
        # Try servers in order of likelihood
        servers_to_try = ["IND", "PK", "BD", "SG"]
        for test_server in servers_to_try:
            tokens = load_tokens(test_server)
            if tokens and len(tokens) > 0:
                encrypted_uid = enc(uid)
                if encrypted_uid:
                    # Try with first token to test if UID exists on this server
                    result = make_request(encrypted_uid, test_server, tokens[0]["token"])
                    if result is not None:
                        server_name = test_server
                        app.logger.info(f"✓ Found UID {uid} on server {test_server}")
                        break
                        
        if not server_name:
            return unicode_jsonify({"error": f"UID {uid} not found on any available server"}, 404)

    try:
        async def process_request_async():
            tokens = load_tokens(server_name)
            if tokens is None:
                raise Exception("Failed to load tokens.")
            
            # Try multiple tokens if first one fails
            token_used = None
            before = None
            encrypted_uid = None
            
            for i, token_data in enumerate(tokens[:5]):  # Try first 5 tokens
                token = token_data["token"]
                encrypted_uid = enc(uid)
                
                app.logger.info(f"Trying token {i+1}/5 for UID {uid}")
                before = make_request(encrypted_uid, server_name, token)
                
                if before is not None:
                    token_used = token
                    app.logger.info(f"Successfully got player info with token {i+1}")
                    break
                else:
                    app.logger.warning(f"Token {i+1} failed for UID {uid}")
            
            if before is None:
                raise Exception(f"Failed to retrieve initial player info with {min(5, len(tokens))} tokens. Server: {server_name}, UID: {uid}")

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))

            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name == "PK":
                url = "https://clientbp.ggblueshark.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            # Send likes with improved rate limiting handling - ASYNC
            likes_sent = await send_multiple_requests(uid, server_name, url)
            app.logger.info(f"💫 Attempted to send likes for UID {uid}, successful requests: {likes_sent if likes_sent else 0}")

            # Use the same working token for final check
            after = make_request(encrypted_uid, server_name, token_used)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            
            # ADVANCED NICKNAME PROCESSING - Get raw data from protobuf
            try:
                # Extract raw nickname data directly from protobuf (before JSON conversion)
                raw_nickname_data = after.AccountInfo.PlayerNickname if hasattr(after.AccountInfo, 'PlayerNickname') else ""
                
                # Use advanced nickname processor for perfect Unicode handling
                player_name = nickname_processor.process_raw_nickname(raw_nickname_data, player_uid)
                
                # Get detailed debug info
                debug_info = nickname_processor.get_display_info(player_name)
                app.logger.info(f"🎮 UID {player_uid} | Raw: {repr(raw_nickname_data)} | Final: {repr(player_name)}")
                app.logger.info(f"📊 Nickname Info: Length={debug_info['length']}, Categories={debug_info['unicode_categories']}")
                
                # RECORD TO DATABASE FIRST (before response)
                save_success = save_player_record(
                    uid=player_uid,
                    nickname=player_name,
                    server_name=server_name,
                    likes_count=after_like
                )
                
                if save_success:
                    app.logger.info(f"💾 Database: Successfully recorded UID {player_uid} nickname: {player_name}")
                else:
                    app.logger.error(f"💾 Database: Failed to record UID {player_uid}")
                
            except Exception as e:
                app.logger.error(f"❌ Critical nickname processing error for UID {player_uid}: {e}")
                # Emergency fallback
                player_name = f"Player_{player_uid}"
            like_given = after_like - before_like
            
            # Improved status logic
            if like_given > 0:
                status = 1
                message = f"✅ Successfully added {like_given} likes!"
            elif likes_sent and likes_sent > 0:
                status = 3  # Likes sent but not reflected (server processing delay)
                message = f"⏳ {likes_sent} like requests sent successfully - likes may appear with delay"
            else:
                status = 2
                message = "❌ No likes were sent"

            response_data = {
                "status": status,
                "message": message,
                "server_detected": server_name,
                "requests_sent": likes_sent if likes_sent else 0,
                "player": {
                    "uid": player_uid,
                    "nickname": player_name,
                },
                "likes": {
                    "before": before_like,
                    "after": after_like,
                    "added_by_api": like_given,
                },
            }
            return response_data

        # Run async function in thread pool for Flask compatibility  
        def run_async():
            return asyncio.run(process_request_async())
            
        with ThreadPoolExecutor() as executor:
            result = executor.submit(run_async).result()
            
        return unicode_jsonify(result)
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return unicode_jsonify({"error": str(e)}, 500)


# Simple status endpoint (no web interface)
@app.route('/')
def status():
    """Simple status message"""
    return unicode_jsonify({
        "service": "Free Fire Token Generator",
        "status": "running",
        "message": "Automatic token generation is active - generating tokens every 4 hours",
        "regions": ["India (IND)", "Pakistan (PK)", "Bangladesh (BD)", "Singapore (SG)"],
        "features": [
            "Auto-detect correct server for any UID",
            "Multi-region support with 210+ real tokens",
            "Use ALL available tokens for maximum likes",
            "Real-time token generation every 4 hours"
        ],
        "usage": {
            "endpoint": "/like?uid=YOUR_UID",
            "auto_detect": "/like?uid=2942087766",
            "manual_server": "/like?uid=2942087766&server_name=PK"
        }
    })

@app.route('/tokens')
def view_tokens():
    """View generated tokens with clean nicknames"""
    try:
        region = request.args.get("region", "").upper()
        
        tokens_data = {}
        
        if region == "IND" or not region:
            try:
                with open("tokens/ind.json", 'r') as f:
                    ind_tokens = json.load(f)
                    tokens_data["india"] = {
                        "total": len(ind_tokens),
                        "tokens": ind_tokens[:10] if len(ind_tokens) > 10 else ind_tokens  # Show first 10
                    }
            except:
                tokens_data["india"] = {"total": 0, "tokens": []}
        
        if region == "PK" or not region:
            try:
                with open("tokens/pk.json", 'r') as f:
                    pk_tokens = json.load(f)
                    tokens_data["pakistan"] = {
                        "total": len(pk_tokens),
                        "tokens": pk_tokens[:10] if len(pk_tokens) > 10 else pk_tokens  # Show first 10
                    }
            except:
                tokens_data["pakistan"] = {"total": 0, "tokens": []}
        
        return unicode_jsonify({
            "status": "success",
            "message": "Generated tokens with clean nicknames",
            "data": tokens_data
        })
        
    except Exception as e:
        return unicode_jsonify({"error": str(e)}, 500)


# Initialize token generation when app starts
def initialize_token_generator():
    """Initialize token generator when app starts"""
    try:
        start_token_generation()
        print("Token generator started successfully")
    except Exception as e:
        print(f"Failed to start token generator: {e}")

# Start the token generator
initialize_token_generator()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
