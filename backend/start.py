#!/usr/bin/env python3
"""
Startup script for Railway deployment
"""
import os
import sys
import uvicorn

def main():
    print("🚀 Starting Health Insights AI Backend...")
    
    # Check environment
    print(f"Python version: {sys.version}")
    print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    
    # Check if we can import the main app
    try:
        from main import app
        print("✅ Main app imported successfully")
    except Exception as e:
        print(f"❌ Error importing main app: {e}")
        sys.exit(1)
    
    # Check if we can import key modules
    try:
        from database import engine, Base
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Error importing database: {e}")
    
    try:
        from routes.auth import router as auth_router
        print("✅ Auth router imported successfully")
    except Exception as e:
        print(f"❌ Error importing auth router: {e}")
    
    try:
        from routes.report import router as report_router
        print("✅ Report router imported successfully")
    except Exception as e:
        print(f"❌ Error importing report router: {e}")
    
    try:
        from routes.chat import router as chat_router
        print("✅ Chat router imported successfully")
    except Exception as e:
        print(f"❌ Error importing chat router: {e}")
    
    try:
        from routes.wearable import router as wearable_router
        print("✅ Wearable router imported successfully")
    except Exception as e:
        print(f"❌ Error importing wearable router: {e}")
    
    # Start the server
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🌐 Starting server on {host}:{port}")
    print("⏳ Waiting 2 seconds for app to fully initialize...")
    
    import time
    time.sleep(2)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
