import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from main import app

def handler(event, context):
    """
    Netlify function handler
    """
    # Import Serverless WSGI handler
    try:
        from serverless_wsgi import handle_request
        return handle_request(app, event, context)
    except ImportError:
        # Fallback for basic deployment
        return {
            'statusCode': 200,
            'body': '{"message": "Free Fire Token Generator is running. Install serverless-wsgi for full functionality."}'
        }