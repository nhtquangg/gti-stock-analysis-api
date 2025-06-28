# config.py - Configuration for GTI Stock Analysis API

from typing import List
import os
from datetime import datetime, timedelta

class GTIConfig:
    """
    🚀 GTI Stock Analysis API Configuration
    """
    
    # 🌐 API Configuration
    API_TITLE = "🚀 GTI Stock Analysis API"
    API_DESCRIPTION = "API phân tích chứng khoán Việt Nam với hệ thống GTI + Pattern Detection miễn phí"
    API_VERSION = "3.0.0"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    # Support both PORT (Render) and API_PORT (local development)
    API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", 8000)))
    
    # 📊 Stock Data Configuration
    DEFAULT_START_DATE = "2024-01-01"
    DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
    VNSTOCK_SOURCE = "VCI"
    DATA_HISTORY_DAYS = 365
    
    # 🔧 GTI System Parameters
    GTI_EMA_SHORT = 10
    GTI_EMA_LONG = 20
    GTI_EMA_MID = 50
    GTI_EMA_LONG_TERM = 200
    GTI_VOLUME_MULTIPLIER = 1.5
    GTI_HIGH_DISTANCE_THRESHOLD = 15  # %
    GTI_PULLBACK_THRESHOLD = 2.0  # %
    
    # 🆓 Pattern Detection Configuration
    PATTERN_WINDOW_SIZE = 20
    VOLUME_SPIKE_MULTIPLIER = 2.0
    TREND_ANALYSIS_DAYS = 5
    DOJI_BODY_RATIO = 0.1
    HAMMER_SHADOW_RATIO = 2.0
    
    # 📈 Trading Strategy Parameters
    MAX_HOLDING_PERIOD = 30  # days
    TARGET_PROFIT_MIN = 10   # %
    TARGET_PROFIT_MAX = 25   # %
    STOP_LOSS_MIN = 5       # %
    STOP_LOSS_MAX = 8       # %
    
    # 🎯 Scoring System
    BULLISH_PATTERNS = [
        "bullish_engulfing", "morning_star", "hammer", 
        "resistance_breakout", "gap_up", "strong_uptrend"
    ]
    
    BEARISH_PATTERNS = [
        "bearish_engulfing", "evening_star", "hanging_man", 
        "support_breakdown", "gap_down"
    ]
    
    NEUTRAL_PATTERNS = ["doji", "volume_spike"]
    
    # 📊 Score Thresholds
    SCORE_VERY_POSITIVE = 4    # 🟢 RẤT TÍCH CỰC
    SCORE_POSITIVE = 2         # 🟡 TÍCH CỰC  
    SCORE_NEUTRAL = 0          # 🟠 TRUNG TÍNH
    # < 0                      # 🔴 TIÊU CỰC
    
    # 🚀 Performance Configuration
    ENABLE_CACHE = True
    CACHE_EXPIRY_MINUTES = 5
    MAX_CONCURRENT_REQUESTS = 10
    
    # 📱 API Endpoints
    ENDPOINTS = {
        "root": "/",
        "basic_analysis": "/phan-tich/{ma_co_phieu}",
        "full_analysis": "/full-analysis/{ma_co_phieu}",
        "gti_info": "/gti-info",
        "patterns_info": "/patterns-info",
        "docs": "/docs",
        "redoc": "/redoc"
    }
    
    # 🎯 VN30 Stocks for Testing
    VN30_STOCKS = [
        "ACB", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", 
        "HPG", "MBB", "MSN", "MWG", "PLX", "POW", "SAB", "SSI", 
        "STB", "TCB", "TPB", "VCB", "VHM", "VIB", "VIC", "VJC", 
        "VNM", "VPB", "VRE", "VSH", "VTI", "VTO"
    ]
    
    # 🔍 Common Stock Symbols for Quick Testing
    POPULAR_STOCKS = ["FPT", "VIC", "VHM", "HPG", "VCB", "BID", "MWG", "VNM"]
    
    @classmethod
    def get_date_range(cls, days_back: int = None) -> tuple:
        """
        Get date range for data fetching
        """
        if days_back is None:
            days_back = cls.DATA_HISTORY_DAYS
            
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    
    @classmethod
    def get_score_evaluation(cls, total_score: int) -> dict:
        """
        Get evaluation based on total score
        """
        if total_score >= cls.SCORE_VERY_POSITIVE:
            return {
                "level": "very_positive",
                "color": "green",
                "emoji": "🟢",
                "message": "RẤT TÍCH CỰC - CÂN NHẮC MUA",
                "action": "BUY"
            }
        elif total_score >= cls.SCORE_POSITIVE:
            return {
                "level": "positive", 
                "color": "yellow",
                "emoji": "🟡",
                "message": "TÍCH CỰC - THEO DÕI",
                "action": "WATCH"
            }
        elif total_score >= cls.SCORE_NEUTRAL:
            return {
                "level": "neutral",
                "color": "orange", 
                "emoji": "🟠",
                "message": "TRUNG TÍNH - CHỜ TÍN HIỆU",
                "action": "HOLD"
            }
        else:
            return {
                "level": "negative",
                "color": "red",
                "emoji": "🔴", 
                "message": "TIÊU CỰC - TRÁNH XA",
                "action": "AVOID"
            }

# 🌍 Environment-specific configurations
class DevelopmentConfig(GTIConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(GTIConfig):
    DEBUG = False
    LOG_LEVEL = "INFO"
    ENABLE_CACHE = True

class TestingConfig(GTIConfig):
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    CACHE_EXPIRY_MINUTES = 1

# 🔧 Get configuration based on environment
def get_config():
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Export default config
config = get_config() 