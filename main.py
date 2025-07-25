from flask import Flask, request, Response, render_template_string
import asyncio
import json
import os
from datetime import datetime
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
from real_token_generator import real_token_generator, start_token_generation, stop_token_generation, get_generator_status, generate_tokens_now, generate_single_token
try:
    from models import db, PlayerRecord, TokenRecord
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Database models not available: {e}")
    DATABASE_AVAILABLE = False
from nickname_processor import nickname_processor

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configure custom Neon database
custom_database_url = "postgresql://neondb_owner:npg_2wvRQWkasIr9@ep-old-king-a1qaotvu-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
os.environ["DATABASE_URL"] = custom_database_url
app.config["SQLALCHEMY_DATABASE_URI"] = custom_database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

# Initialize database with Flask app
if DATABASE_AVAILABLE:
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
        print("✅ Using custom Neon database for data storage")
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        DATABASE_AVAILABLE = False

# Internal storage for player records - NO EXTERNAL DATABASE
player_records = {}

def save_player_record(uid, nickname, server_name, likes_count):
    """Save player record to PostgreSQL database with proper app context"""
    try:
        if DATABASE_AVAILABLE:
            with app.app_context():
                # Convert UID to string to match database schema
                uid_str = str(uid)
                
                # Check if record exists
                existing_record = PlayerRecord.query.filter_by(uid=uid_str, server_name=server_name).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.nickname = nickname
                    existing_record.likes_count = likes_count
                    existing_record.last_updated = datetime.utcnow()
                else:
                    # Create new record
                    new_record = PlayerRecord(
                        uid=uid_str,
                        nickname=nickname,
                        server_name=server_name,
                        likes_count=likes_count
                    )
                    db.session.add(new_record)
                
                db.session.commit()
                app.logger.info(f"📝 Custom Neon DB: UID {uid}: {nickname}")
                return True
        else:
            # Fallback to internal storage
            player_records[f"{uid}_{server_name}"] = {
                "uid": str(uid),
                "nickname": nickname,
                "server_name": server_name,
                "likes_count": likes_count,
                "last_updated": datetime.utcnow().isoformat()
            }
            app.logger.info(f"📝 Internal storage: UID {uid}: {nickname}")
            return True
    except Exception as e:
        app.logger.error(f"❌ Database error for UID {uid}: {e}")
        return False


@app.route("/records", methods=["GET"])
def get_records():
    """Get all player records from custom Neon database"""
    try:
        if DATABASE_AVAILABLE:
            # Get records from custom Neon database
            records = PlayerRecord.query.order_by(PlayerRecord.last_updated.desc()).limit(100).all()
            records_list = [record.to_dict() for record in records]
            return unicode_jsonify({
                "total_records": len(records_list),
                "records": records_list,
                "message": "Custom Neon Database Storage"
            })
        else:
            # Fallback to internal storage
            records_list = list(player_records.values())
            records_list.sort(key=lambda x: x.get('last_updated', ''), reverse=True)
            return unicode_jsonify({
                "total_records": len(records_list),
                "records": records_list[:100],
                "message": "Internal bot storage"
            })
    except Exception as e:
        app.logger.error(f"Database query error: {e}")
        return unicode_jsonify({"error": str(e)}, 500)

@app.route("/generate_token", methods=["POST", "GET"])
def manual_token_generation():
    """Manual token generation endpoint for testing"""
    if request.method == "GET":
        # Show simple form for testing
        return """
        <html>
        <head><title>Manual Token Generation</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Manual JWT Token Generation</h2>
            <form method="POST">
                <p><label>UID (10 digits):</label><br>
                <input type="text" name="uid" placeholder="4059499797" style="width: 200px; padding: 5px;"></p>
                
                <p><label>Password (64 char hex):</label><br> 
                <input type="text" name="password" placeholder="90692811391BDC1BCAB416B78DB4293300A797E38CA8A3FD4526E538FECFAC39" style="width: 500px; padding: 5px;"></p>
                
                <p><input type="submit" value="Generate Token" style="padding: 10px 20px; background: #007cba; color: white; border: none;"></p>
            </form>
        </body>
        </html>
        """
    
    # Handle POST request
    uid = request.form.get("uid") or request.json.get("uid") if request.is_json else None
    password = request.form.get("password") or request.json.get("password") if request.is_json else None
    
    if not uid or not password:
        return unicode_jsonify({"error": "UID and password are required"}, 400)
    
    try:
        app.logger.info(f"Manual token generation requested for UID: {uid}")
        token_result = generate_single_token(uid, password)
        
        if token_result:
            return unicode_jsonify({
                "success": True,
                "uid": uid,
                "token": token_result["token"],
                "message": "JWT token generated successfully"
            })
        else:
            return unicode_jsonify({
                "success": False,
                "uid": uid,
                "error": "Failed to generate token - check UID/password format and validity"
            }, 400)
            
    except Exception as e:
        app.logger.error(f"Manual token generation error: {str(e)}")
        return unicode_jsonify({
            "success": False,
            "error": f"Generation failed: {str(e)}"
        }, 500)

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
            with app.app_context():
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
            with app.app_context():
                tokens = load_tokens(server_name)
                if tokens is None or len(tokens) == 0:
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
            with app.app_context():
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
    """View generated tokens from custom Neon database and files"""
    try:
        region = request.args.get("region", "").upper()
        tokens_data = {}
        
        # Try to get tokens from database first (CUSTOM NEON DATABASE)
        if DATABASE_AVAILABLE:
            try:
                with app.app_context():
                    if region == "IND" or not region:
                        ind_tokens = TokenRecord.query.filter_by(server_name='IND', is_active=True).limit(10).all()
                        tokens_data["india"] = {
                            "total": TokenRecord.query.filter_by(server_name='IND', is_active=True).count(),
                            "tokens": [{"token": t.token, "uid": t.uid, "generated_at": t.generated_at.isoformat()} for t in ind_tokens]
                        }
                    
                    if region == "PK" or not region:
                        pk_tokens = TokenRecord.query.filter_by(server_name='PK', is_active=True).limit(10).all()
                        tokens_data["pakistan"] = {
                            "total": TokenRecord.query.filter_by(server_name='PK', is_active=True).count(),
                            "tokens": [{"token": t.token, "uid": t.uid, "generated_at": t.generated_at.isoformat()} for t in pk_tokens]
                        }
                        
                    if tokens_data:
                        app.logger.info(f"✅ Retrieved tokens from custom Neon database: {tokens_data.get('india', {}).get('total', 0)} IND + {tokens_data.get('pakistan', {}).get('total', 0)} PK")
                        return unicode_jsonify({
                            "status": "success",
                            "message": f"Retrieved from custom Neon database",
                            "source": "database",
                            "data": tokens_data
                        })
            except Exception as db_error:
                app.logger.warning(f"Database token retrieval failed, falling back to files: {str(db_error)}")
        
        # Database-only approach - no file fallback
        return unicode_jsonify({
            "status": "error",
            "message": "No tokens found in custom Neon database",
            "source": "database_only",
            "data": {"india": {"total": 0, "tokens": []}, "pakistan": {"total": 0, "tokens": []}}
        })
        
    except Exception as e:
        return unicode_jsonify({"error": f"Failed to retrieve tokens: {str(e)}"}, 500)


# Initialize token generation when app starts (only if not on Vercel)
def initialize_token_generator():
    """Initialize token generator when app starts"""
    try:
        # Skip token generation on Vercel to avoid timeouts
        if not os.environ.get('VERCEL'):
            start_token_generation()
            print("Token generator started successfully")
        else:
            print("Running on Vercel - skipping automatic token generation")
    except Exception as e:
        print(f"Failed to start token generator: {e}")

# Start the token generator (only in non-Vercel environments)
initialize_token_generator()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
