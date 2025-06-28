#!/usr/bin/env python3
# start.py - 🚀 GTI Stock Analysis API Startup Script

import os
import sys
import logging
import uvicorn
from datetime import datetime

# Import configuration
try:
    from config import config
except ImportError:
    print("❌ Cannot import config. Make sure config.py exists.")
    sys.exit(1)

def setup_logging():
    """
    🔧 Setup logging configuration
    """
    log_level = getattr(config, 'LOG_LEVEL', 'INFO')
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Console handler  
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # Only add file logging in development, skip in production to avoid file watcher issues
    if environment == 'development':
        # Create logs directory if not exists
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler
        file_handler = logging.FileHandler(
            f"{log_dir}/gti_api_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    
    return root_logger

def print_startup_info():
    """
    📊 Print startup information
    """
    print("\n" + "="*60)
    print("🚀 GTI STOCK ANALYSIS API")
    print("="*60)
    print(f"📊 Version: {config.API_VERSION}")
    print(f"🌐 Host: {config.API_HOST}")
    print(f"🔌 Port: {config.API_PORT}")
    print(f"🔧 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n📚 API Endpoints:")
    print(f"   🏠 Root: http://{config.API_HOST}:{config.API_PORT}/")
    print(f"   📊 Analysis: http://{config.API_HOST}:{config.API_PORT}/full-analysis/FPT")
    print(f"   📖 Docs: http://{config.API_HOST}:{config.API_PORT}/docs")
    print(f"   🔍 ReDoc: http://{config.API_HOST}:{config.API_PORT}/redoc")
    print("\n🎯 Quick Test Commands:")
    print(f"   curl http://{config.API_HOST}:{config.API_PORT}/full-analysis/FPT")
    print(f"   curl http://{config.API_HOST}:{config.API_PORT}/gti-info")
    print("="*60)

def check_dependencies():
    """
    🔍 Check if all required dependencies are available
    """
    required_modules = [
        'fastapi', 'uvicorn', 'pandas', 'numpy', 'ta', 'vnstock'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing required modules: {', '.join(missing_modules)}")
        print("📦 Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are available")
    return True

def main():
    """
    🚀 Main function to start the API server
    """
    # Setup logging
    logger = setup_logging()
    logger.info("🚀 Starting GTI Stock Analysis API...")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Print startup info
    print_startup_info()
    
    # Get configuration
    host = config.API_HOST
    port = config.API_PORT
    debug = getattr(config, 'DEBUG', False)
    
    # Force disable reload in production environment
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    enable_reload = debug and environment != 'production'
    
    # Start server
    try:
        logger.info(f"🌐 Starting server on {host}:{port}")
        logger.info(f"🔧 Environment: {environment}")
        logger.info(f"🔄 Auto-reload: {enable_reload}")
        uvicorn.run(
            "main_api:app",
            host=host,
            port=port,
            reload=enable_reload,
            log_level="info",
            access_log=True,
            loop="auto"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
        print("\n👋 GTI API stopped. Goodbye!")
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 