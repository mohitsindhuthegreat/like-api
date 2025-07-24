from flask import Flask, request, jsonify, Response, render_template_string
import asyncio
import json
import os
from google.protobuf.json_format import MessageToJson
from app.utils import load_tokens
from app.encryption import enc
from app.request_handler import make_request, send_multiple_requests
from simple_token_generator import simple_token_generator, start_token_generation, stop_token_generation, get_generator_status, generate_tokens_now

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


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
                raise Exception("Failed to load tokens.")
            token = tokens[0]["token"]
            encrypted_uid = enc(uid)

            before = make_request(encrypted_uid, server_name, token)
            if before is None:
                raise Exception("Failed to retrieve initial player info.")

            data_before = json.loads(MessageToJson(before))
            before_like = int(data_before.get("AccountInfo", {}).get("Likes", 0))

            if server_name == "IND":
                url = "https://client.ind.freefiremobile.com/LikeProfile"
            elif server_name in {"BR", "US", "SAC", "NA"}:
                url = "https://client.us.freefiremobile.com/LikeProfile"
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
        return jsonify({"error": str(e)}), 500


# Token Generator Endpoints
@app.route('/tokens/status', methods=['GET'])
def token_status():
    """Get token generator status"""
    try:
        status = get_generator_status()
        return jsonify({
            "status": "success",
            "generator": status,
            "message": "Token generator is running" if status["is_running"] else "Token generator is stopped"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tokens/start', methods=['POST'])
def start_tokens():
    """Start automatic token generation"""
    try:
        start_token_generation()
        return jsonify({
            "status": "success",
            "message": "Token generation started successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tokens/stop', methods=['POST'])
def stop_tokens():
    """Stop automatic token generation"""
    try:
        stop_token_generation()
        return jsonify({
            "status": "success",
            "message": "Token generation stopped successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tokens/generate', methods=['POST'])
def generate_tokens_endpoint():
    """Manually trigger token generation"""
    try:
        generate_tokens_now()
        return jsonify({
            "status": "success",
            "message": "Token generation triggered successfully"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tokens/info', methods=['GET'])
def tokens_info():
    """Get information about available tokens"""
    try:
        info = {}
        regions = ["ind", "pk"]
        
        for region in regions:
            try:
                with open(f"tokens/{region}.json", 'r') as f:
                    tokens = json.load(f)
                    info[region] = {
                        "count": len(tokens),
                        "last_generated": tokens[0].get("generated_at", "Unknown") if tokens else "No tokens"
                    }
            except FileNotFoundError:
                info[region] = {"count": 0, "last_generated": "No file found"}
            except Exception as e:
                info[region] = {"count": 0, "error": str(e)}
        
        return jsonify({
            "status": "success",
            "tokens_info": info
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def dashboard():
    """Simple dashboard for monitoring token generation"""
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Free Fire Token Generator Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 20px; margin: 10px 0; border-radius: 5px; }
            .success { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .warning { background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
            .error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            button { padding: 10px 20px; margin: 5px; border: none; border-radius: 3px; cursor: pointer; }
            .btn-success { background-color: #28a745; color: white; }
            .btn-danger { background-color: #dc3545; color: white; }
            .btn-primary { background-color: #007bff; color: white; }
            .tokens-info { margin: 20px 0; }
            .region { margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Free Fire Token Generator Dashboard</h1>
            
            <div class="status success">
                <h3>🔄 Automatic Token Generation System</h3>
                <p>This system automatically generates authentication tokens for Free Fire accounts every 4 hours.</p>
                <p><strong>Supported Regions:</strong> India (IND), Pakistan (PK)</p>
            </div>
            
            <div class="controls">
                <h3>Controls</h3>
                <button class="btn-success" onclick="startGenerator()">Start Generator</button>
                <button class="btn-danger" onclick="stopGenerator()">Stop Generator</button>
                <button class="btn-primary" onclick="generateNow()">Generate Now</button>
                <button class="btn-primary" onclick="refreshStatus()">Refresh Status</button>
            </div>
            
            <div id="status-info"></div>
            <div id="tokens-info"></div>
            
            <div class="status warning">
                <h3>📋 How It Works</h3>
                <ul>
                    <li>Reads account credentials from IND_ACC.json and PK_ACC.json</li>
                    <li>Generates authentication tokens for each account</li>
                    <li>Saves tokens to tokens/ind.json and tokens/pk.json</li>
                    <li>Automatically repeats every 4 hours</li>
                    <li>Logs all activities for monitoring</li>
                </ul>
            </div>
        </div>
        
        <script>
            function makeRequest(url, method = 'GET') {
                return fetch(url, { method: method })
                    .then(response => response.json())
                    .catch(error => ({ error: error.message }));
            }
            
            function startGenerator() {
                makeRequest('/tokens/start', 'POST').then(data => {
                    alert(data.message || data.error);
                    refreshStatus();
                });
            }
            
            function stopGenerator() {
                makeRequest('/tokens/stop', 'POST').then(data => {
                    alert(data.message || data.error);
                    refreshStatus();
                });
            }
            
            function generateNow() {
                if (confirm('This will generate tokens for all accounts. Continue?')) {
                    makeRequest('/tokens/generate', 'POST').then(data => {
                        alert(data.message || data.error);
                        refreshStatus();
                    });
                }
            }
            
            function refreshStatus() {
                // Get generator status
                makeRequest('/tokens/status').then(data => {
                    const statusDiv = document.getElementById('status-info');
                    if (data.status === 'success') {
                        const isRunning = data.generator.is_running;
                        statusDiv.innerHTML = `
                            <div class="status ${isRunning ? 'success' : 'warning'}">
                                <h3>Generator Status: ${isRunning ? '🟢 Running' : '🔴 Stopped'}</h3>
                                <p>Jobs scheduled: ${data.generator.jobs_count}</p>
                                <p>Next run: ${data.generator.next_run || 'Not scheduled'}</p>
                            </div>
                        `;
                    } else {
                        statusDiv.innerHTML = `<div class="status error"><h3>Error getting status: ${data.error}</h3></div>`;
                    }
                });
                
                // Get tokens info
                makeRequest('/tokens/info').then(data => {
                    const tokensDiv = document.getElementById('tokens-info');
                    if (data.status === 'success') {
                        let html = '<div class="tokens-info"><h3>Token Information</h3>';
                        for (const [region, info] of Object.entries(data.tokens_info)) {
                            html += `
                                <div class="region">
                                    <strong>${region.toUpperCase()}:</strong> 
                                    ${info.count} tokens available
                                    <br>Last generated: ${info.last_generated}
                                    ${info.error ? `<br>Error: ${info.error}` : ''}
                                </div>
                            `;
                        }
                        html += '</div>';
                        tokensDiv.innerHTML = html;
                    } else {
                        tokensDiv.innerHTML = `<div class="status error"><h3>Error getting tokens info: ${data.error}</h3></div>`;
                    }
                });
            }
            
            // Auto refresh every 30 seconds
            setInterval(refreshStatus, 30000);
            
            // Initial load
            refreshStatus();
        </script>
    </body>
    </html>
    """
    return dashboard_html


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
