"""
Production-ready server using Waitress (Windows compatible)
Run this instead of app.py for better Windows support
"""
from waitress import serve
from app import app
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"Starting Flask server with Waitress...")
    print(f"Server running on http://{host}:{port}")
    print(f"Health check: http://{host}:{port}/health")
    print("Press CTRL+C to quit")
    
    serve(app, host=host, port=port)