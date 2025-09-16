#!/usr/bin/env python3
"""
Production startup script for Supreme Keeper League Flask App
Uses Waitress WSGI server for production deployment
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_production_server():
    """Start the production server using Waitress"""
    
    # Import app after environment is loaded
    from app import app
    
    try:
        import waitress
        
        # Get configuration from environment or use defaults
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', 5000))
        threads = int(os.getenv('WAITRESS_THREADS', '4'))
        
        print("=" * 60)
        print("🚀 SUPREME KEEPER LEAGUE - PRODUCTION SERVER")
        print("=" * 60)
        print(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
        print(f"Debug Mode: {os.getenv('FLASK_DEBUG', 'False')}")
        print(f"Server: Waitress WSGI Server")
        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"Threads: {threads}")
        print(f"Database: {os.getenv('DATABASE_URL', 'keeper.db')}")
        print("=" * 60)
        print("Starting production server...")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start Waitress server
        waitress.serve(
            app, 
            host=host, 
            port=port, 
            threads=threads,
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120
        )
        
    except ImportError:
        print("❌ Waitress not installed. Install with: pip install waitress")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting production server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_production_server()
