"""
Vercel-optimized Flask API entry point for Free Fire Token Generator
"""
import os
import sys

# Set Vercel environment flag
os.environ['VERCEL'] = '1'

# Add the parent directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from main.py
from main import app

# Vercel serverless function handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request.environ, lambda *args: None)

# Vercel expects the Flask app to be available as 'app'
# This file serves as the entry point for Vercel deployment
if __name__ == "__main__":
    app.run(debug=False)