#!/usr/bin/env python3
"""
Server runner script for the Unit Test Generator Backend.
This script provides a convenient way to start the FastAPI server with proper configuration.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    """Run the FastAPI server with appropriate configuration."""
    
    # Check if we're in the correct directory
    current_dir = Path.cwd()
    if not (current_dir / "app.py").exists():
        print("Error: app.py not found in current directory.")
        print("Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set.")
        print("   Please set your Gemini API key:")
        print("   export GOOGLE_API_KEY='your_actual_api_key'")
        print()
    
    print("🚀 Starting Unit Test Generator Backend...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("⚡ Server URL: http://localhost:8000")
    print()
    
    try:
        # Run the server with appropriate settings
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()