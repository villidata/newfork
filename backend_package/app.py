#!/usr/bin/env python3
"""
FastAPI Backend Entry Point for cPanel Hosting
This file serves as the main entry point for the FastAPI application
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Import the FastAPI app from server.py
from server import app

# This is the WSGI application object that cPanel/hosting will use
application = app

if __name__ == "__main__":
    import uvicorn
    # For local development
    uvicorn.run(app, host="0.0.0.0", port=8001)