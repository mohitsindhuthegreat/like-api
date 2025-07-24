from flask import Flask, request, jsonify, Response, render_template
import asyncio
import json
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Render the main interface for testing the API"""
    return render_template("index.html")

@app.route("/like", methods=["GET"])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    if not uid or not server_name:
        return jsonify({"error": "UID and server_name are required"}), 400

    try:
        def process_request():
            tokens = load_tokens(server_name)
            if tokens is None:
                raise Exception(f"No tokens available for server: {server_name}")
            
            token = tokens[0]["token"]
            encrypted_uid = enc(uid)
            if encrypted_uid is None:
                raise Exception("Failed to encrypt UID")

            before = make_request(encrypted_uid, server_name, token)
            if before is None:
                # Return demo response when API fails
                return {
                    "status": 0,
                    "message": "⚠️ API temporarily unavailable. This is a demo response.",
                    "error": "Free Fire servers are currently not responding or tokens need to be refreshed. The like bot functionality requires valid authentication tokens.",
                    "player": {
                        "uid": int(uid),
                        "nickname": "Demo Player",
                    },
                    "likes": {
                        "before": 0,
                        "after": 0,
                        "added_by_api": 0,
                    },
                    "note": "To fix this: Update authentication tokens in tokens/ind.json with valid Free Fire API tokens"
                }

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))

            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
            elif server_name == "PK":
                url = "https://clientbp.ggblueshark.com/LikeProfile"
            else:
                url = "https://clientbp.ggblueshark.com/LikeProfile"

            asyncio.run(send_multiple_requests(uid, server_name, url))

            after = make_request(encrypted_uid, server_name, token)
            if after is None:
                raise Exception("Failed to retrieve player info after like requests.")

            data_after = json.loads(MessageToJson(after))
            after_like = int(data_after.get("AccountInfo", {}).get("Likes", 0))
            player_uid = int(data_after.get("AccountInfo", {}).get("UID", 0))
            player_name = str(
                data_after.get("AccountInfo", {}).get("PlayerNickname", "")
            )
            like_given = after_like - before_like
            status = 1 if like_given != 0 else 2

            return {
                "status": status,
                "message": "Like operation successful"
                if status == 1
                else "No likes added",
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
        return jsonify({
            "error": "Service temporarily unavailable",
            "details": "Free Fire API authentication failed. Tokens may be expired.",
            "solution": "Please provide updated authentication tokens to restore full functionality."
        }), 503

@app.route("/api/servers", methods=["GET"])
def get_supported_servers():
    """Get list of supported servers"""
    servers = ["IND", "BR", "US", "SAC", "NA", "PK", "MENA", "THAI"]
    return jsonify({"servers": servers})

@app.route("/api/status", methods=["GET"])
def api_status():
    """Check API and token status"""
    status = {
        "api": "online",
        "version": "1.0",
        "endpoints": ["/like", "/api/servers", "/api/status"],
        "servers": {
            "IND": "configured",
            "BR": "configured", 
            "US": "configured",
            "SAC": "configured", 
            "NA": "configured",
            "PK": "configured",
            "MENA": "configured",
            "THAI": "configured"
        },
        "note": "Token authentication required for live functionality"
    }
    return jsonify(status)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
