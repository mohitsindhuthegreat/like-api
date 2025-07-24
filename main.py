import os
import logging
from flask import Flask, request, jsonify, Response, render_template
import asyncio
import json
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")

@app.route("/", methods=["GET"])
def index():
    """Render the main interface for testing the API"""
    return render_template("index.html")

@app.route("/like", methods=["GET"])
def handle_requests():
    """
    Handle Free Fire like requests
    Parameters:
    - uid: Player UID to send likes to
    - server_name: Server name (IND, BR, US, SAC, NA, etc.)
    """
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    
    if not uid or not server_name:
        return jsonify({"error": "UID and server_name are required"}), 400
    
    try:
        def process_request():
            # Load tokens for the specified server
            tokens = load_tokens(server_name)
            if tokens is None:
                raise Exception("Failed to load tokens.")
            
            token = tokens[0]["token"]
            encrypted_uid = enc(uid)
            
            # Get player info before sending likes
            before = make_request(encrypted_uid, server_name, token)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")
            
            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))
            
            # Determine the correct API endpoint based on server
            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"
            
            # Send multiple like requests asynchronously
            asyncio.run(send_multiple_requests(uid, server_name, url))
            
            # Get player info after sending likes
            after = make_request(encrypted_uid, server_name, token)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")
            
            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            player_name = str(data_after.get("AccountInfo", {}).get("PlayerNickname", ""))
            
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2
            
            return {
                "status": status,
                "message": "Like operation successful" if status == 1 else "No likes added",
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
            json.dumps(result, indent=2, sort_keys=False), 
            mimetype="application/json"
        )
        
    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/servers", methods=["GET"])
def get_supported_servers():
    """Get list of supported servers"""
    servers = ["IND", "BR", "US", "SAC", "NA", "MENA", "THAI"]
    return jsonify({"servers": servers})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
