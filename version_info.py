# version_info.py - 🚀 GTI Stock Analysis API Version Information

from datetime import datetime

# 📊 Version Information
VERSION_MAJOR = 3
VERSION_MINOR = 0
VERSION_PATCH = 0
VERSION_BUILD = "2024.12.28"

# 🔧 Full version string
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"
VERSION_FULL = f"{VERSION}.{VERSION_BUILD}"

# 📅 Build Information
BUILD_DATE = "2024-12-28"
BUILD_TIME = datetime.now().strftime("%H:%M:%S")
BUILD_TIMESTAMP = datetime.now().isoformat()

# 🎯 Release Information
RELEASE_NAME = "GTI Pattern Detection"
RELEASE_CODENAME = "Golden Eagle"
RELEASE_TYPE = "stable"  # alpha, beta, rc, stable

# 🌟 Features in this version
FEATURES = [
    "GTI Analysis System (Growth Trading Intelligence)",
    "12 Free Pattern Detection algorithms",
    "Combined GTI + Pattern scoring system",
    "FastAPI with Swagger documentation",
    "Docker containerization support",
    "VN30 stock market support",
    "Real-time analysis capabilities",
    "Custom GPT integration ready"
]

# 🔧 System Requirements
REQUIREMENTS = {
    "python": ">=3.8",
    "fastapi": ">=0.115.0",
    "pandas": ">=2.0.0",
    "numpy": ">=1.24.0",
    "ta": ">=0.11.0",
    "vnstock": ">=3.2.0"
}

# 📚 API Information
API_INFO = {
    "title": "🚀 GTI Stock Analysis API",
    "description": "API phân tích chứng khoán Việt Nam với hệ thống GTI + Pattern Detection miễn phí",
    "version": VERSION,
    "contact": {
        "name": "GTI Analysis Team",
        "url": "https://github.com/your-username/stock-gti-analysis",
        "email": "support@gti-analysis.com"
    },
    "license": {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
}

# 🎯 Change Log (Latest changes first)
CHANGELOG = {
    "3.0.0": {
        "date": "2024-12-28",
        "type": "major",
        "changes": [
            "✨ Added 12 free pattern detection algorithms",
            "🚀 Implemented GTI (Growth Trading Intelligence) system",
            "📊 Combined scoring system GTI + Patterns",
            "🔥 Full API with /full-analysis endpoint",
            "🐳 Docker containerization support",
            "📚 Comprehensive documentation and examples",
            "🎯 Custom GPT integration ready",
            "⚡ Async support for high performance"
        ]
    },
    "2.0.0": {
        "date": "2024-12-20",
        "type": "major", 
        "changes": [
            "🔧 GTI system implementation",
            "📈 Basic pattern detection",
            "🌐 FastAPI integration"
        ]
    },
    "1.0.0": {
        "date": "2024-12-01",
        "type": "initial",
        "changes": [
            "🎉 Initial release",
            "📊 Basic stock analysis",
            "🔌 vnstock integration"
        ]
    }
}

def get_version_info():
    """
    📊 Get complete version information
    """
    return {
        "version": VERSION,
        "version_full": VERSION_FULL,
        "build_date": BUILD_DATE,
        "build_time": BUILD_TIME,
        "build_timestamp": BUILD_TIMESTAMP,
        "release_name": RELEASE_NAME,
        "release_codename": RELEASE_CODENAME,
        "release_type": RELEASE_TYPE,
        "features": FEATURES,
        "requirements": REQUIREMENTS,
        "api_info": API_INFO
    }

def get_build_banner():
    """
    🎨 Get formatted build banner for console output
    """
    banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                  🚀 GTI Stock Analysis API                   ║
╠══════════════════════════════════════════════════════════════╣
║  Version: {VERSION_FULL:<45}  ║
║  Release: {RELEASE_NAME} ({RELEASE_CODENAME}){' '*(45-len(RELEASE_NAME)-len(RELEASE_CODENAME)-3)}║
║  Build Date: {BUILD_DATE:<42}  ║
║  Type: {RELEASE_TYPE:<47}  ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 GTI + Pattern Detection System for VN Stock Market      ║
║  📊 12 Free Patterns + 4-Point GTI Scoring                  ║
║  🚀 FastAPI + Docker Ready + Custom GPT Support             ║
╚══════════════════════════════════════════════════════════════╝
"""
    return banner

def print_version_info():
    """
    🖨️  Print version information to console
    """
    print(get_build_banner())
    print(f"\n📚 Features in this version:")
    for feature in FEATURES:
        print(f"   • {feature}")
    
    print(f"\n🔧 System Requirements:")
    for req, version in REQUIREMENTS.items():
        print(f"   • {req}: {version}")
    
    print(f"\n📅 Latest Changes:")
    latest_version = list(CHANGELOG.keys())[0]
    latest_changes = CHANGELOG[latest_version]
    print(f"   Version {latest_version} ({latest_changes['date']}):")
    for change in latest_changes['changes'][:5]:  # Show top 5 changes
        print(f"     {change}")

if __name__ == "__main__":
    print_version_info() 