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
    
    # 🔍 Market Scanning Configuration - RATE LIMIT PROTECTED
    MARKET_SCAN_BATCH_SIZE = 8          # Giảm từ 30 xuống 8 để tránh rate limiting
    MARKET_SCAN_TIMEOUT = 900           # Tăng timeout lên 15 phút do có rate limiting delays
    SINGLE_STOCK_TIMEOUT = 30           # Tăng timeout cho từng mã (rate limiter cần thời gian)
    MIN_GTI_SCORE_FOR_SCAN = 2          # Điểm GTI tối thiểu để lọc
    MIN_COMBINED_SCORE_FOR_SCAN = 3     # Điểm tổng hợp tối thiểu
    MAX_RESULTS_RETURN = 50             # Tối đa 50 kết quả trả về
    
    # 🛡️ Rate Limiting Protection (NEW)
    ENABLE_RATE_LIMITING = True         # Bật rate limiting protection
    RATE_LIMIT_DELAY = 1.0              # Delay tối thiểu giữa các API calls (giây)
    RATE_LIMIT_MAX_RETRIES = 3          # Số lần retry khi gặp rate limit
    SEQUENTIAL_SCAN_MODE = False        # Scan tuần tự thay vì parallel (khi cần)
    
    # 🚀 Performance Optimization 
    CHUNK_SIZE_FOR_LARGE_SCANS = 20     # Giảm chunk size để tránh overwhelm API
    ENABLE_PROGRESSIVE_TIMEOUT = True   # Tăng timeout dần cho scans lớn
    TOP_PICKS_QUICK_MODE = True         # Mode nhanh cho top picks
    CACHE_SINGLE_STOCK_RESULTS = True   # Cache kết quả từng mã để giảm API calls
    
    # 📱 API Endpoints
    ENDPOINTS = {
        "root": "/",
        "basic_analysis": "/phan-tich/{ma_co_phieu}",
        "full_analysis": "/full-analysis/{ma_co_phieu}",
        "market_scan": "/market-scan",              # 🆕 ENDPOINT MỚI
        "market_scan_vn30": "/market-scan/vn30",    # 🆕 SCAN VN30
        "market_scan_custom": "/market-scan/custom", # 🆕 SCAN CUSTOM LIST
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
    
    # 🎯 Sector Classification - Expanded to ~40 stocks per sector
    SECTOR_STOCKS = {
        "banking": [
            # Big banks
            "VCB", "BID", "CTG", "VPB", "TCB", "ACB", "MBB", "TPB", "HDB", "STB",
            # Medium banks
            "VIB", "SHB", "EIB", "LPB", "SSB", "OCB", "MSB", "NVB", "VBB", "ABB",
            # Smaller banks
            "BAB", "BVB", "CBB", "IVB", "KLB", "NAB", "PGB", "SGB", "TLB", "VDB",
            # Financial services
            "BFC", "CFC", "FID", "PSI", "SVC", "TVD", "VFS", "WSS", "ASA", "BIC"
        ],
        
        "real_estate": [
            # Large developers
            "VHM", "VIC", "VRE", "NVL", "DXG", "KDH", "HDG", "BCM", "DGC", "PDR",
            # Medium developers
            "QCG", "NLG", "HNG", "CEO", "IJC", "DIG", "AGG", "CII", "HDC", "IDI",
            # Construction & materials
            "CTD", "HBC", "ROS", "PC1", "LCG", "CKG", "VCG", "FCN", "SZC", "SCG",
            # Infrastructure
            "VGC", "D2D", "TDH", "SZL", "NBB", "TTC", "THG", "MVN", "KBC", "HDG"
        ],
        
        "technology": [
            # IT Services
            "FPT", "CMG", "EFI", "ITD", "VTI", "SAM", "CMT", "VGI", "CTR", "DTD",
            # Telecom
            "VGI", "ELC", "MFS", "SGT", "NET", "FOX", "VNT", "VTC", "ICT", "AME",
            # Tech hardware
            "MWG", "DGW", "VCS", "QTC", "DST", "TNG", "MCV", "SPI", "VPH", "PHC",
            # Software & digital
            "VCI", "BSI", "VND", "HCM", "CTS", "ORS", "APS", "VIX", "DSC", "VSI"
        ],
        
        "manufacturing": [
            # Steel & metals
            "HPG", "HSG", "NKG", "TVN", "SMC", "VGS", "POM", "TIS", "VCA", "DTL",
            # Chemicals & materials
            "DGC", "CSV", "AAA", "DPM", "BMP", "DGW", "SFG", "TYA", "VFG", "PVT",
            # Electronics
            "SAM", "VTK", "ELC", "VHC", "PHR", "MCV", "DST", "VCS", "SPI", "VPH",
            # Machinery
            "DHC", "DMC", "HII", "VMC", "THI", "VTO", "GMC", "VRC", "CKG", "VGC"
        ],
        
        "consumer": [
            # Retail
            "MWG", "FRT", "PNJ", "DGW", "VCS", "QTC", "GMD", "DST", "VEA", "PET",
            # Food & beverages
            "VNM", "MSN", "SAB", "MCH", "VHC", "LAF", "QNS", "DBC", "VCF", "FMC",
            # Personal care
            "TNG", "UNI", "NET", "PHR", "DHP", "YEG", "MCV", "VPH", "PHC", "IMP",
            # Tourism & entertainment
            "VJC", "HVN", "VNG", "DAH", "VTO", "TCO", "FIT", "ASM", "TSC", "CTC"
        ],
        
        "energy": [
            # Oil & gas
            "GAS", "PLX", "PVS", "PVD", "BSR", "PVC", "PVB", "PSH", "PVG", "GEG",
            # Power generation
            "POW", "NT2", "PC1", "EVN", "VNE", "SBA", "TBC", "HND", "QTP", "MVN",
            # Renewable energy
            "REE", "GEG", "SBA", "TBC", "HND", "QTP", "MVN", "NBC", "DTK", "BWE",
            # Mining
            "SVN", "MVN", "DTK", "TDW", "NBC", "SMA", "BMC", "TKU", "HSL", "TMC"
        ],
        
        "securities": [
            # Large securities
            "SSI", "VCI", "VND", "HCM", "BSI", "CTS", "MBS", "VDS", "SHS", "TVS",
            # Medium securities
            "ORS", "APS", "VIX", "AGR", "FTS", "VFS", "DSC", "VSI", "PHS", "WSS",
            # Asset management
            "VFG", "DLG", "PSI", "SVC", "BVS", "IFS", "VIG", "DXS", "VEA", "TVD",
            # Investment
            "IDI", "IJC", "CEO", "VGI", "VPG", "VRC", "VMG", "VSC", "VTB", "VHL"
        ],
        
        "construction": [
            # Construction
            "ROS", "CTD", "HBC", "LCG", "PC1", "CKG", "VCG", "FCN", "SZC", "SCG",
            # Infrastructure
            "CII", "HDC", "TDH", "SZL", "NBB", "TTC", "THG", "MVN", "D2D", "VGC",
            # Materials
            "BMP", "CSV", "DPM", "HPG", "HSG", "NKG", "TVN", "SMC", "VGS", "TIS",
            # Engineering
            "DHC", "DMC", "HII", "VMC", "THI", "GMC", "VRC", "LAS", "SEC", "SVC"
        ],
        
        "utilities": [
            # Power & electricity
            "POW", "REE", "GEG", "NT2", "PC1", "EVN", "VNE", "SBA", "TBC", "HND",
            # Water & waste
            "TDW", "NBC", "BWE", "SMA", "BMC", "TKU", "HSL", "TMC", "DTK", "MVN",
            # Transport utilities
            "VTO", "GMD", "VJC", "HVN", "TSC", "TCO", "CTC", "VOS", "VST", "PVT",
            # Other utilities
            "QTP", "MVN", "NBC", "DTK", "BWE", "SMA", "BMC", "TKU", "HSL", "TMC"
        ],
        
        "transportation": [
            # Airlines
            "VJC", "HVN", "VNA", "ASM", "FIT", "TSC", "TCO", "CTC", "VOS", "VST",
            # Shipping & logistics
            "VTO", "GMD", "VST", "VOS", "PVT", "VIP", "HAH", "SVI", "HAG", "HAS",
            # Port services
            "VIP", "HAH", "SVI", "HAG", "HAS", "CLL", "PHP", "DVP", "GMC", "VRC",
            # Transportation infrastructure
            "CII", "VGC", "D2D", "TDH", "NBB", "TTC", "THG", "MVN", "LAS", "SEC"
        ]
    }
    
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
    
    @classmethod
    def get_stock_list_by_type(cls, list_type: str = "vn30") -> list:
        """
        Get stock list by type - SECTOR-BASED APPROACH
        """
        if list_type.lower() == "vn30":
            return cls.VN30_STOCKS
        elif list_type.lower() == "popular":
            return cls.POPULAR_STOCKS
        elif list_type.lower() in cls.SECTOR_STOCKS:
            return cls.SECTOR_STOCKS[list_type.lower()]
        else:
            return cls.VN30_STOCKS  # Default
    
    @classmethod
    def get_all_sectors_combined(cls, limit_per_sector: int = None) -> list:
        """
        Get stocks from all sectors combined - for top picks scanning
        """
        all_stocks = []
        for sector_name, stocks in cls.SECTOR_STOCKS.items():
            if limit_per_sector:
                all_stocks.extend(stocks[:limit_per_sector])
            else:
                all_stocks.extend(stocks)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_stocks = []
        for stock in all_stocks:
            if stock not in seen:
                seen.add(stock)
                unique_stocks.append(stock)
        
        return unique_stocks
    
    @classmethod
    def get_all_sectors(cls) -> dict:
        """
        Get all sector information
        """
        return cls.SECTOR_STOCKS

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