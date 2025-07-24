from flask import Flask, request, jsonify, Response, render_template_string
import asyncio
import json
import os
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
from real_token_generator import real_token_generator, start_token_generation, stop_token_generation, get_generator_status, generate_tokens_now

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


@app.route("/like", methods=["GET"])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    
    # Allow auto-detection if server_name is not provided
    if not uid:
        return jsonify({"error": "UID is required"}), 400
    
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
            return jsonify({"error": f"UID {uid} not found on any available server"}), 404

    try:

        def process_request():
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

            asyncio.run(send_multiple_requests(uid, server_name, url))

            # Use the same working token for final check
            after = make_request(encrypted_uid, server_name, token_used)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            
            # Enhanced nickname extraction and decoding
            raw_player_name = data_after.get("AccountInfo", {}).get("PlayerNickname", "")
            
            # Robust Unicode handling and decoding for all scenarios
            try:
                player_name = raw_player_name
                
                # Handle different data types
                if isinstance(raw_player_name, bytes):
                    # Try different encoding methods for bytes
                    for encoding in ['utf-8', 'utf-16', 'latin1', 'cp1252']:
                        try:
                            player_name = raw_player_name.decode(encoding)
                            break
                        except:
                            continue
                elif isinstance(raw_player_name, str):
                    # Handle potential encoding issues in strings
                    player_name = raw_player_name
                    
                    # Fix common Unicode escape sequences that might be corrupted
                    import codecs
                    try:
                        # Try to decode Unicode escape sequences if present
                        player_name = codecs.decode(player_name, 'unicode_escape')
                    except:
                        pass
                else:
                    # Convert other types to string
                    player_name = str(raw_player_name)
                
                # Normalize Unicode characters to handle variations
                import unicodedata
                try:
                    player_name = unicodedata.normalize('NFC', player_name)
                except:
                    pass
                
                # Remove problematic control characters but keep visible Unicode
                import re
                # Only remove actual control characters, not Unicode letters/symbols
                player_name = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', player_name)
                
                # Clean up whitespace
                player_name = player_name.strip()
                
                # Provide fallback only if completely empty
                if not player_name:
                    player_name = f"Player_{player_uid}"
                    
                # Enhanced logging for debugging
                app.logger.info(f"Nickname processing - Raw: {repr(raw_player_name)} ({type(raw_player_name)}) -> Final: {repr(player_name)}")
                    
            except Exception as e:
                app.logger.error(f"Error processing nickname for UID {player_uid}: {e}")
                player_name = f"Player_{player_uid}"
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2

            return {
                "status": status,
                "message": "Like operation successful"
                if status == 1
                else "No likes added",
                "server_detected": server_name,
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

        result = process_request()
        return Response(
            json.dumps(result, indent=2, sort_keys=False), mimetype="application/json"
        )
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500


# Simple status endpoint (no web interface)
@app.route('/')
def status():
    """Simple status message"""
    return jsonify({
        "service": "Free Fire Token Generator",
        "status": "running",
        "message": "Automatic token generation is active - generating tokens every 4 hours",
        "regions": ["India (IND)", "Pakistan (PK)", "Bangladesh (BD)", "Singapore (SG)"],
        "features": [
            "Auto-detect correct server for any UID",
            "Multi-region support with 100+ real tokens",
            "Automatic like sending (100 likes per request)",
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
        
        return jsonify({
            "status": "success",
            "message": "Generated tokens with clean nicknames",
            "data": tokens_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
