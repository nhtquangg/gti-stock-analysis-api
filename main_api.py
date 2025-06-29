# main_api.py

import pandas as pd
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from typing import Optional

# Import các hàm từ file lay_data_stock.py
from lay_data_stock import (
    lay_du_lieu_co_phieu_vnstock, 
    tinh_toan_chi_bao_ky_thuat,
    detect_free_patterns,
    detect_large_chart_patterns,
    phan_tich_pattern_results,
    get_market_context,
    get_sector_analysis,
    comprehensive_gti_analysis,
    prepare_news_search_context,
    market_scan_parallel,
    market_scan_by_category,
    market_scan_top_picks,
    scan_single_stock
)

from config import GTIConfig

# 🚀 Import Cache Manager
from cache_manager import gti_cache, cache_stock_analysis, cache_market_scan

# 🔄 Import Task Manager for Async Processing
from task_manager import task_manager

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="🚀 GTI Stock Analysis API",
    description="API phân tích chứng khoán Việt Nam với hệ thống GTI (Growth Trading Intelligence) + Pattern Detection miễn phí",
    version="3.0.0",
    contact={
        "name": "GTI Analysis System",
        "url": "https://github.com/nhtquangg/gti-stock-analysis-api",
    },
)

@app.get("/")
def read_root():
    return {
        "message": "🚀 Chào mừng đến với GTI Stock Analysis API!",
        "he_thong": "GTI PRO v3.0 - Growth Trading Intelligence + Market Scanner",
        "phien_ban": "3.3.0",
        "tinh_nang": [
            "🔥 GTI Core Analysis (4 tiêu chí cốt lõi)",
            "🎯 Enhanced Pattern Detection (16 patterns: 12 basic + 4 large)",
            "🌊 Market Context Analysis (VNINDEX + Sector)",
            "📰 News Search Integration (cho ChatGPT)",
            "⚡ Combined Scoring (-5 to +18 range)",
            "🚀 Comprehensive Analysis API",
            "🔍 Market Scanner - Quét toàn bộ thị trường",
            "🏆 Top Picks - Tìm mã tốt nhất",
            "🏢 Sector Analysis - Phân tích theo ngành",
            "🎯 Custom List Scanning"
        ],
        "endpoints": {
            "individual_analysis": {
                "/phan-tich/{ma_co_phieu}": "Phân tích GTI cơ bản",
                "/full-analysis/{ma_co_phieu}": "🚀 GTI PRO v3.0 - Phân tích toàn diện",
                "/news-context/{ma_co_phieu}": "News search context cho ChatGPT"
            },
            "market_scanning": {
                "/market-scan": "🔍 Quét thị trường theo danh mục (VN30, ngành, popular)",
                "/market-scan/vn30": "🎯 Quick VN30 scan với tiêu chí cao",
                "/market-scan/top-picks": "🏆 TOP picks từ tất cả sectors",
                "/market-scan/sector/{sector}": "🏢 Quét theo ngành cụ thể (~40 mã)",
                "/market-scan/custom": "🎯 Quét danh sách tùy chỉnh",
                "/market-scan/quick-check/{stock}": "⚡ Kiểm tra nhanh một mã"
            },
            "async_market_scanning": {
                "POST /market-scan/start": "🚀 Bắt đầu tác vụ quét bất đồng bộ (tránh timeout)",
                "GET /market-scan/status/{task_id}": "🔍 Kiểm tra trạng thái tác vụ",
                "GET /market-scan/result/{task_id}": "📊 Lấy kết quả khi hoàn thành",
                "/tasks/stats": "📊 Thống kê task manager"
            },
            "system_info": {
                "/gti-info": "Thông tin về hệ thống GTI",
                "/patterns-info": "Thông tin về 16 patterns (12 basic + 4 large)"
            }
        },
        "vi_du_su_dung": {
            "phan_tich_don_le": "/full-analysis/FPT",
            "quet_vn30_nhanh": "/market-scan/vn30",
            "top_picks_dong_bo": "/market-scan/top-picks?limit=10",
            "quet_ngan_hang": "/market-scan/sector/banking",
            "quet_tuy_chinh_nho": "/market-scan/custom?stocks=FPT,VIC,HPG,VCB",
            "kiem_tra_nhanh": "/market-scan/quick-check/FPT"
        },
        "vi_du_async": {
            "bat_dau_top_picks": "POST /market-scan/start?task_type=top_picks&limit=15",
            "bat_dau_sector_scan": "POST /market-scan/start?task_type=sector_scan&sector=banking",
            "kiem_tra_trang_thai": "GET /market-scan/status/{task_id}",
            "lay_ket_qua": "GET /market-scan/result/{task_id}",
            "note": "🚀 Dùng async cho scans lớn (>20 mã) để tránh timeout"
        },
        "danh_muc_ho_tro": {
            "stock_lists": ["vn30", "popular"],
            "sectors": ["banking", "real_estate", "technology", "manufacturing", "consumer", "energy", "securities", "construction", "utilities", "transportation"],
            "sector_sizes": {
                "banking": "40 mã (từ big banks đến financial services)",
                "real_estate": "40 mã (developers, construction, infrastructure)",
                "technology": "40 mã (IT services, telecom, hardware, software)",
                "manufacturing": "40 mã (steel, chemicals, electronics, machinery)",
                "consumer": "40 mã (retail, F&B, personal care, tourism)",
                "energy": "40 mã (oil & gas, power, renewable, mining)",
                "securities": "40 mã (securities firms, asset management)",
                "construction": "40 mã (construction, infrastructure, materials)",
                "utilities": "40 mã (power, water, transport utilities)",
                "transportation": "40 mã (airlines, shipping, logistics, ports)"
            }
        }
    }

@app.get("/phan-tich/{ma_co_phieu}")
def phan_tich_co_phieu(ma_co_phieu: str):
    """
    Endpoint phân tích GTI cơ bản cho một mã cổ phiếu.
    
    Returns:
        Phân tích GTI với điểm số 0-4 và tín hiệu BUY/HOLD/AVOID
    """
    # Tính toán thời gian lấy dữ liệu (1 năm từ hiện tại)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Lấy dữ liệu
    df = lay_du_lieu_co_phieu_vnstock(
        ma_co_phieu=ma_co_phieu.upper(),
        start_date=start_date,
        end_date=end_date
    )
    
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã: {ma_co_phieu}")
    
    # Tính toán chỉ báo GTI
    df_analyzed = tinh_toan_chi_bao_ky_thuat(df)
    
    # Lấy kết quả của ngày giao dịch gần nhất
    latest = df_analyzed.iloc[-1]
    
    # Chuẩn bị kết quả trả về theo format GTI
    result = {
        # Thông tin cơ bản
        "ma_co_phieu": ma_co_phieu.upper(),
        "ngay_cap_nhat": latest.name.strftime("%Y-%m-%d") if hasattr(latest.name, 'strftime') else str(latest.name),
        "gia_dong_cua": round(float(latest['close']), 2),
        "gia_cao_nhat": round(float(latest['high']), 2),
        "gia_thap_nhat": round(float(latest['low']), 2),
        "khoi_luong": int(latest['volume']) if pd.notna(latest['volume']) else 0,
        
        # Các đường EMA theo GTI
        "EMA10": round(float(latest['EMA10']), 2) if pd.notna(latest['EMA10']) else None,
        "EMA20": round(float(latest['EMA20']), 2) if pd.notna(latest['EMA20']) else None,
        "EMA50": round(float(latest['EMA50']), 2) if pd.notna(latest['EMA50']) else None,
        "EMA200": round(float(latest['EMA200']), 2) if pd.notna(latest['EMA200']) else None,
        
        # Các chỉ số GTI chính
        "gti_trend_check": bool(latest['gti_trend_check']) if pd.notna(latest['gti_trend_check']) else False,
        "gti_recent_breakout": bool(latest['gti_recent_breakout']) if pd.notna(latest['gti_recent_breakout']) else False,
        "gti_dist_to_high_percent": round(float(latest['gti_dist_to_high_percent']), 2) if pd.notna(latest['gti_dist_to_high_percent']) else None,
        "gti_is_pullback": bool(latest['gti_is_pullback']) if pd.notna(latest['gti_is_pullback']) else False,
        
        # Tổng kết GTI
        "gti_score": int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0,
        "gti_signal": str(latest['gti_signal']) if pd.notna(latest['gti_signal']) else "HOLD",
        
        # Metadata
        "he_thong": "GTI - Growth Trading Intelligence",
        "phien_ban": "3.0.0",
        "ghi_chu": "Phân tích GTI cơ bản. Sử dụng /full-analysis/{ma_co_phieu} để có pattern detection."
    }

    return result

@app.get("/full-analysis/{ma_co_phieu}")
def full_analysis_co_phieu(ma_co_phieu: str):
    """
    🚀 Endpoint phân tích GTI PRO v2.0 TOÀN DIỆN
    
    Includes:
    - GTI Core (4 tiêu chí) + Enhanced Patterns (16 patterns)
    - Market Context (VNINDEX) + Sector Analysis  
    - News Search Context cho ChatGPT
    - Combined Scoring (-5 to +18 range)
    """
    try:
        # Sử dụng comprehensive analysis function mới
        result = comprehensive_gti_analysis(ma_co_phieu.upper())
        
        if result['status'] == 'error':
            raise HTTPException(status_code=404, detail=result['message'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phân tích comprehensive cho {ma_co_phieu}: {str(e)}")

@app.get("/full-analysis-legacy/{ma_co_phieu}")
def full_analysis_legacy(ma_co_phieu: str):
    """
    🔥 Endpoint phân tích ĐẦY ĐỦ GTI + Pattern Detection (Legacy version)
    
    Returns:
        Phân tích tổng hợp GTI + 12 patterns miễn phí + điểm tổng hợp
    """
    try:
        # Tính toán thời gian lấy dữ liệu (1 năm từ hiện tại)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Lấy dữ liệu
        df = lay_du_lieu_co_phieu_vnstock(
            ma_co_phieu=ma_co_phieu.upper(),
            start_date=start_date,
            end_date=end_date
        )
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã: {ma_co_phieu}")
        
        # Tính toán chỉ báo GTI
        df_analyzed = tinh_toan_chi_bao_ky_thuat(df)
        
        # Phát hiện patterns miễn phí
        df_patterns = detect_free_patterns(df_analyzed)
        
        # 🔥 THÊM: Phát hiện large chart patterns
        df_patterns = detect_large_chart_patterns(df_patterns)
        
        # Phân tích kết quả patterns
        pattern_results = phan_tich_pattern_results(df_patterns, ma_co_phieu.upper())
        
        # 🌊 THÊM: Lấy bối cảnh thị trường và ngành
        market_context = get_market_context()
        sector_analysis = get_sector_analysis(ma_co_phieu.upper())
        
        # Lấy kết quả của ngày giao dịch gần nhất
        latest = df_patterns.iloc[-1]
        
        # Safe date formatting
        try:
            if hasattr(latest.name, 'strftime'):
                ngay_cap_nhat = latest.name.strftime("%Y-%m-%d")
            else:
                ngay_cap_nhat = str(latest.name)
        except:
            ngay_cap_nhat = datetime.now().strftime("%Y-%m-%d")
        
        # Tính điểm tổng hợp - đảm bảo tất cả là int Python
        gti_score = int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0
        bullish_score = int(pattern_results.get('bullish_score', 0))
        bearish_score = int(pattern_results.get('bearish_score', 0))
        tong_diem = int(gti_score + bullish_score - bearish_score)
        
        # Đánh giá tổng hợp
        if tong_diem >= 4:
            danh_gia = "🟢 RẤT TÍCH CỰC - CÂN NHẮC MUA"
            mau_sac = "green"
        elif tong_diem >= 2:
            danh_gia = "🟡 TÍCH CỰC - THEO DÕI"
            mau_sac = "yellow"
        elif tong_diem >= 0:
            danh_gia = "🟠 TRUNG TÍNH - CHỜ TÍN HIỆU"
            mau_sac = "orange"
        else:
            danh_gia = "🔴 TIÊU CỰC - TRÁNH XA"
            mau_sac = "red"
        
        # Chuẩn bị kết quả trả về
        result = {
            # Thông tin cơ bản
            "ma_co_phieu": ma_co_phieu.upper(),
            "ngay_cap_nhat": ngay_cap_nhat,
            "gia_dong_cua": round(float(latest['close']), 2),
            "khoi_luong": int(latest['volume']) if pd.notna(latest['volume']) else 0,
            
            # GTI Analysis
            "gti_analysis": {
                "gti_trend_check": bool(latest['gti_trend_check']) if pd.notna(latest['gti_trend_check']) else False,
                "gti_recent_breakout": bool(latest['gti_recent_breakout']) if pd.notna(latest['gti_recent_breakout']) else False,
                "gti_dist_to_high_percent": round(float(latest['gti_dist_to_high_percent']), 2) if pd.notna(latest['gti_dist_to_high_percent']) else None,
                "gti_is_pullback": bool(latest['gti_is_pullback']) if pd.notna(latest['gti_is_pullback']) else False,
                "gti_score": gti_score,
                "gti_signal": str(latest['gti_signal']) if pd.notna(latest['gti_signal']) else "HOLD"
            },
            
            # Pattern Analysis
            "pattern_analysis": {
                "bullish_score": bullish_score,
                "bearish_score": bearish_score,
                "current_patterns": pattern_results.get('current_patterns', []),
                "pattern_summary": f"{bullish_score}B/{bearish_score}Be"
            },
            
            # Kết hợp GTI + Patterns
            "combined_analysis": {
                "tong_diem": tong_diem,
                "danh_gia": danh_gia,
                "mau_sac": mau_sac,
                "chi_tiet": f"GTI: {gti_score}/4 + Pattern: {bullish_score}B/{bearish_score}Be"
            },
            
            # Support/Resistance Levels
            "levels": {
                "support_level": round(float(latest['support_level']), 2) if pd.notna(latest['support_level']) else None,
                "resistance_level": round(float(latest['resistance_level']), 2) if pd.notna(latest['resistance_level']) else None,
                "EMA10": round(float(latest['EMA10']), 2) if pd.notna(latest['EMA10']) else None,
                "EMA20": round(float(latest['EMA20']), 2) if pd.notna(latest['EMA20']) else None
            },
            
            # 🌊 Market Context & Sector Analysis
            "market_context": market_context,
            "sector_analysis": sector_analysis,
            
            # Metadata
            "he_thong": "GTI + Pattern Detection + Market Context",
            "phien_ban": "3.1.0",
            "timestamp": datetime.now().isoformat()
        }

        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý dữ liệu cho {ma_co_phieu}: {str(e)}")

@app.get("/news-context/{ma_co_phieu}")
def get_news_context(ma_co_phieu: str):
    """
    📰 Endpoint cho ChatGPT lấy news search context
    
    Returns:
        Context và hướng dẫn search tin tức cho ChatGPT
    """
    try:
        # Lấy thông tin ngành
        sector_analysis = get_sector_analysis(ma_co_phieu.upper())
        sector_name = sector_analysis.get('sector_name') if sector_analysis.get('status') == 'success' else None
        
        # Tạo news search context
        news_context = prepare_news_search_context(ma_co_phieu.upper(), sector_name)
        
        return {
            "stock_symbol": ma_co_phieu.upper(),
            "sector_info": {
                "sector_name": sector_name,
                "status": sector_analysis.get('status', 'unknown')
            },
            "news_search_context": news_context,
            "important_note": "📊 Tất cả dữ liệu về giá, volume, chỉ số kỹ thuật đã được cung cấp qua API - CHỈ search tin tức và sự kiện!"
        }
        
    except Exception as e:
        return {
            "error": f"Lỗi tạo news context cho {ma_co_phieu}: {str(e)}",
            "fallback_context": prepare_news_search_context(ma_co_phieu.upper(), None)
        }

@app.get("/patterns-info")
def patterns_info():
    """
    Thông tin về 16 patterns được sử dụng (12 basic + 4 large)
    """
    return {
        "title": "🎯 16 Chart Patterns Detection",
        "version": "Enhanced v2.0",
        "basic_patterns": {
            "candlestick_patterns": [
                {"name": "Doji", "description": "Nến doji - biểu hiện sự do dự của thị trường", "points": 0},
                {"name": "Hammer", "description": "Nến búa - tín hiệu đảo chiều tăng", "points": "+1"},
                {"name": "Hanging Man", "description": "Nến treo cổ - tín hiệu đảo chiều giảm", "points": "-1"}
            ],
            "engulfing_patterns": [
                {"name": "Bullish Engulfing", "description": "Nến bao phủ tăng - tín hiệu mạnh", "points": "+1"},
                {"name": "Bearish Engulfing", "description": "Nến bao phủ giảm - tín hiệu yếu", "points": "-1"}
            ],
            "star_patterns": [
                {"name": "Morning Star", "description": "Sao mai - 3 nến đảo chiều tăng", "points": "+1"},
                {"name": "Evening Star", "description": "Sao hôm - 3 nến đảo chiều giảm", "points": "-1"}
            ],
            "breakout_patterns": [
                {"name": "Resistance Breakout", "description": "Vượt kháng cự với volume cao", "points": "+1"},
                {"name": "Support Breakdown", "description": "Thủng hỗ trợ với volume cao", "points": "-1"}
            ],
            "volume_patterns": [
                {"name": "Volume Spike", "description": "Khối lượng bất thường > 2x trung bình", "points": 0}
            ],
            "gap_patterns": [
                {"name": "Gap Up", "description": "Gap tăng với momentum", "points": "+1"},
                {"name": "Gap Down", "description": "Gap giảm với momentum", "points": "-1"}
            ],
            "trend_patterns": [
                {"name": "Strong Uptrend", "description": "Xu hướng tăng mạnh 5 ngày", "points": "+1"}
            ]
        },
        "large_patterns": {
            "description": "Large chart patterns (worth 2 points each)",
            "patterns": [
                {"name": "Cup & Handle", "description": "Cup & Handle - mẫu hình chứa sâu + tay cầm", "points": "+2"},
                {"name": "Bull Flag", "description": "Bull Flag - cột cờ + consolidation", "points": "+2"},
                {"name": "Base n' Break", "description": "Base n' Break - tích lũy + breakout", "points": "+2"},
                {"name": "Ascending Triangle", "description": "Ascending Triangle - support tăng dần", "points": "+2"}
            ]
        },
        "scoring_system": {
            "basic_bullish": ["bullish_engulfing", "morning_star", "hammer", "resistance_breakout", "gap_up", "strong_uptrend"],
            "basic_bearish": ["bearish_engulfing", "evening_star", "hanging_man", "support_breakdown", "gap_down"],
            "neutral_patterns": ["doji", "volume_spike"],
            "large_bullish": ["cup_handle", "bull_flag", "base_n_break", "ascending_triangle"],
            "scoring_formula": "GTI (0-4) + Basic Bullish (+1 each) - Basic Bearish (-1 each) + Large Patterns (+2 each) + Market Context Adjustments"
        },
        "total_range": "Score range: -5 to +18 points"
    }

@app.get("/custom-gpt-instructions")
def get_custom_gpt_instructions():
    """
    Endpoint để Custom GPT đọc hướng dẫn từ file custom_gpt.md
    """
    try:
        with open("custom_gpt.md", "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "instructions": content,
            "usage": "Đây là hướng dẫn chi tiết để tích hợp API với Custom GPT",
            "api_base_url": "Sử dụng URL hiện tại của server này",
            "main_endpoints": [
                "/full-analysis/{ma_co_phieu}",
                "/phan-tich/{ma_co_phieu}",
                "/gti-info",
                "/patterns-info"
            ]
        }
    except FileNotFoundError:
        return {"error": "File custom_gpt.md không tồn tại"}
    except Exception as e:
        return {"error": f"Lỗi đọc file: {str(e)}"}

@app.get("/test")
def test_endpoint():
    """Simple test endpoint"""
    return {"status": "OK", "message": "Test endpoint works!"}

@app.get("/test-data/{stock}")
def test_data_only(stock: str):
    """Test data fetching only"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        df = lay_du_lieu_co_phieu_vnstock(stock.upper(), start_date, end_date)
        
        if df is None or df.empty:
            return {"error": "No data", "stock": stock}
        
        return {
            "success": True,
            "stock": stock.upper(),
            "rows": len(df),
            "columns": len(df.columns),
            "last_close": float(df['close'].iloc[-1]),
            "columns_list": list(df.columns)[:5]
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/test-gti/{stock}")
def test_gti_only(stock: str):
    """Test GTI calculation only"""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Step 1: Get data
        df = lay_du_lieu_co_phieu_vnstock(stock.upper(), start_date, end_date)
        if df is None or df.empty:
            return {"error": "No data", "step": 1}
        
        # Step 2: GTI calculation
        df_gti = tinh_toan_chi_bao_ky_thuat(df)
        latest = df_gti.iloc[-1]
        
        return {
            "success": True,
            "stock": stock.upper(),
            "gti_score": int(latest['gti_score']),
            "gti_signal": str(latest['gti_signal']),
            "gti_trend_check": bool(latest['gti_trend_check']),
            "gti_recent_breakout": bool(latest['gti_recent_breakout']),
            "price": float(latest['close'])
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}

@app.get("/debug/{ma_co_phieu}")
def debug_analysis(ma_co_phieu: str):
    """
    Debug endpoint để test từng bước
    """
    try:
        # Step 1: Get data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        df = lay_du_lieu_co_phieu_vnstock(ma_co_phieu.upper(), start_date, end_date)
        if df is None or df.empty:
            return {"error": "Không có dữ liệu", "step": 1}
        
        # Step 2: GTI calculation
        df_gti = tinh_toan_chi_bao_ky_thuat(df)
        
        # Step 3: Pattern detection
        df_patterns = detect_free_patterns(df_gti)
        
        # Step 4: Pattern results
        pattern_results = phan_tich_pattern_results(df_patterns, ma_co_phieu.upper())
        
        # Step 5: Latest data
        latest = df_patterns.iloc[-1]
        
        return {
            "success": True,
            "steps_completed": 5,
            "gti_score": int(latest['gti_score']),
            "bullish_score": pattern_results.get('bullish_score', 0),
            "bearish_score": pattern_results.get('bearish_score', 0),
            "pattern_results_keys": list(pattern_results.keys()) if pattern_results else [],
            "latest_columns": list(latest.index)[:10]  # First 10 columns
        }
        
    except Exception as e:
        return {"error": str(e), "type": str(type(e).__name__)}

@app.get("/gti-info")
def gti_info():
    """
    Thông tin chi tiết về hệ thống GTI
    """
    return {
        "ten_he_thong": "GTI - Growth Trading Intelligence", 
        "muc_tieu": {
            "thoi_gian_nam_giu": "Tối đa 1 tháng",
            "sinh_loi_muc_tieu": "10-25%",
            "cat_lo": "5-8%"
        },
        "tieu_chi_loc": [
            "✅ Xu hướng kỹ thuật: EMA10 > EMA20 và giá nằm trên cả EMA10 & EMA20",
            "✅ Volume & breakout: Có ít nhất 1 phiên breakout với volume > 1.5x TB20",
            "✅ Vị trí giá: Ưu tiên cổ phiếu tiệm cận đỉnh 1 năm (< 15%)",
            "✅ Pullback đúng chuẩn: Sau breakout, pullback về EMA10 hoặc EMA20"
        ],
        "bang_diem_gti": {
            "4_diem": "🟢 RẤT TÍCH CỰC - BUY signal",
            "3_diem": "🟡 TÍCH CỰC - Theo dõi",
            "2_diem": "🟠 TRUNG TÍNH - HOLD",
            "0-1_diem": "🔴 TIÊU CỰC - AVOID"
        },
        "chi_so_tra_ve": {
            "gti_trend_check": "Kiểm tra xu hướng GTI (True/False)",
            "gti_recent_breakout": "Có breakout gần đây không (True/False)",
            "gti_dist_to_high_percent": "Khoảng cách đến đỉnh 1 năm (%)",
            "gti_is_pullback": "Đang pullback về EMA10/20 không (True/False)",
            "gti_score": "Điểm tổng GTI (0-4)",
            "gti_signal": "Tín hiệu GTI (BUY/HOLD/AVOID)"
        }
    }

@app.get("/market-scan")
def market_scan_full(
    category: str = "vn30",
    min_gti_score: int = 2, 
    min_combined_score: int = 3,
    limit: Optional[int] = None
):
    """
    🔍 MARKET SCANNER - Quét thị trường theo danh mục (SECTOR-BASED)
    
    Args:
        category: Loại danh sách (vn30, popular, banking, real_estate, technology, etc.)
        min_gti_score: Điểm GTI tối thiểu (0-4)
        min_combined_score: Điểm tổng hợp tối thiểu (GTI + Pattern)
        limit: Giới hạn số kết quả trả về (mặc định không giới hạn)
    
    Returns:
        Danh sách các mã cổ phiếu đạt tiêu chí GTI, sắp xếp theo điểm số
        
    Available categories:
        - vn30: VN30 stocks (30 mã blue-chip)
        - popular: Popular stocks (8 mã phổ biến) 
        - Sectors (~40 mã mỗi sector):
          * banking, real_estate, technology, manufacturing
          * consumer, energy, securities, construction
          * utilities, transportation
    """
    try:
        print(f"🔍 Market Scan Request: category={category}, min_gti={min_gti_score}, min_combined={min_combined_score}")
        
        # Validate parameters
        if min_gti_score < 0 or min_gti_score > 4:
            raise HTTPException(status_code=400, detail="min_gti_score phải từ 0-4")
        
        if min_combined_score < -5 or min_combined_score > 18:
            raise HTTPException(status_code=400, detail="min_combined_score phải từ -5 đến 18")
        
        # Thực hiện market scan với cache
        scan_result = cache_market_scan(
            category=category,
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        # Kiểm tra lỗi
        if "error" in scan_result:
            raise HTTPException(status_code=400, detail=scan_result["error"])
        
        # Áp dụng limit nếu có
        results = scan_result["scan_results"]
        if limit and limit > 0:
            results = results[:limit]
        
        # Chuẩn bị response
        response = {
            "market_scan_results": {
                "qualified_stocks": results,
                "total_qualified": len(scan_result["scan_results"]),
                "returned_count": len(results),
                "scan_criteria": {
                    "category": category,
                    "min_gti_score": min_gti_score,
                    "min_combined_score": min_combined_score,
                    "limit_applied": limit
                }
            },
            "category_info": scan_result["category_info"],
            "execution_statistics": scan_result["statistics"],
            "market_overview": {
                "scan_time": scan_result["scan_timestamp"],
                "performance_summary": f"Quét {scan_result['statistics']['total_scanned']} mã trong {scan_result['statistics']['execution_time_seconds']}s",
                "success_rate": round(scan_result["statistics"]["success_count"] / scan_result["statistics"]["total_scanned"] * 100, 1) if scan_result["statistics"]["total_scanned"] > 0 else 0
            },
            "api_info": {
                "endpoint": "market-scan",
                "version": "1.0.0",
                "description": "🔍 GTI Market Scanner - Quét thị trường tự động"
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi market scan: {str(e)}")

@app.get("/market-scan/vn30")
def market_scan_vn30_quick(min_gti_score: int = 3, min_combined_score: int = 4):
    """
    🎯 QUICK VN30 SCAN - Quét nhanh VN30 với tiêu chí cao
    
    Returns:
        Top VN30 stocks đạt tiêu chí cao
    """
    try:
        scan_result = market_scan_by_category(
            category="vn30",
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        results = scan_result["scan_results"]
        
        return {
            "vn30_scan": {
                "qualified_stocks": results,
                "total_qualified": len(results),
                "scan_criteria": {
                    "focus": "VN30 - Blue chips",
                    "min_gti_score": min_gti_score,
                    "min_combined_score": min_combined_score
                }
            },
            "quick_summary": {
                "top_3_picks": results[:3] if len(results) >= 3 else results,
                "qualification_rate": f"{len(results)}/30 VN30 stocks",
                "market_sentiment": "Tích cực" if len(results) >= 5 else "Thận trọng" if len(results) >= 2 else "Yếu"
            },
            "execution_time": scan_result["statistics"]["execution_time_seconds"],
            "scan_timestamp": scan_result["scan_timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi VN30 scan: {str(e)}")

@app.get("/market-scan/top-picks")
def market_scan_top_picks_endpoint(limit: int = 15):
    """
    🏆 TOP PICKS - Lấy top mã cổ phiếu tốt nhất từ tất cả sectors
    
    Args:
        limit: Số lượng top picks cần trả về (mặc định 15)
    
    Returns:
        Top picks với phân tích chi tiết và khuyến nghị
        
    Sector-based approach:
        - Quick mode: Quét VN30 + top 10 từ mỗi sector (~130 mã)
        - Normal mode: Quét VN30 + top 20 từ mỗi sector (~230 mã)
        - An toàn hơn, tránh rate limiting, coverage đầy đủ các ngành
    """
    try:
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="Limit phải từ 1-50")
        
        top_picks_result = market_scan_top_picks(limit=limit)
        
        if "message" in top_picks_result:
            return {
                "message": top_picks_result["message"],
                "scan_info": top_picks_result["scan_info"]
            }
        
        return {
            "top_picks_analysis": {
                "top_stocks": top_picks_result["top_picks"],
                "categorized_by_strength": top_picks_result["categorized_picks"],
                "sector_distribution": top_picks_result["sector_distribution"],
                "market_summary": top_picks_result["summary"]
            },
            "investment_recommendation": top_picks_result["recommendation"],
            "scan_performance": top_picks_result["scan_info"],
            "usage_guide": {
                "very_strong_stocks": "Cân nhắc mua với tỷ trọng cao",
                "strong_stocks": "Theo dõi và mua khi có pullback", 
                "moderate_stocks": "Chờ tín hiệu rõ ràng hơn",
                "risk_management": "Luôn đặt stop-loss 5-8%"
            },
            "scan_timestamp": top_picks_result["scan_timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi top picks: {str(e)}")

@app.get("/market-scan/sector/{sector}")
def market_scan_by_sector(
    sector: str,
    min_gti_score: int = 2,
    min_combined_score: int = 3
):
    """
    🏢 SECTOR SCAN - Quét theo ngành cụ thể
    
    Args:
        sector: Tên ngành (banking, real_estate, technology, manufacturing, etc.)
        min_gti_score: Điểm GTI tối thiểu
        min_combined_score: Điểm tổng hợp tối thiểu
    
    Returns:
        Kết quả scan theo ngành với phân tích so sánh
    """
    try:
        # Validate sector
        available_sectors = list(GTIConfig.SECTOR_STOCKS.keys())
        if sector.lower() not in available_sectors:
            raise HTTPException(
                status_code=400, 
                detail=f"Ngành '{sector}' không hợp lệ. Các ngành có sẵn: {available_sectors}"
            )
        
        scan_result = market_scan_by_category(
            category=sector.lower(),
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score
        )
        
        results = scan_result["scan_results"]
        sector_stocks = GTIConfig.SECTOR_STOCKS[sector.lower()]
        
        return {
            "sector_analysis": {
                "sector_name": sector.upper(),
                "qualified_stocks": results,
                "qualification_stats": {
                    "qualified_count": len(results),
                    "total_in_sector": len(sector_stocks),
                    "qualification_rate": f"{len(results)}/{len(sector_stocks)}",
                    "percentage": round(len(results) / len(sector_stocks) * 100, 1) if len(sector_stocks) > 0 else 0
                }
            },
            "sector_performance": {
                "top_performer": results[0] if results else None,
                "average_score": round(sum([s["combined_score"] for s in results]) / len(results), 2) if results else 0,
                "score_distribution": {
                    "excellent": len([s for s in results if s["combined_score"] >= 6]),
                    "good": len([s for s in results if 4 <= s["combined_score"] < 6]),
                    "fair": len([s for s in results if 2 <= s["combined_score"] < 4])
                }
            },
            "execution_info": scan_result["statistics"],
            "scan_timestamp": scan_result["scan_timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi sector scan: {str(e)}")

@app.get("/market-scan/custom")
def market_scan_custom_list(
    stocks: str,
    min_gti_score: int = 2,
    min_combined_score: int = 3
):
    """
    🎯 CUSTOM SCAN - Quét danh sách mã tùy chỉnh
    
    Args:
        stocks: Danh sách mã cổ phiếu cách nhau bởi dấu phẩy (VD: FPT,VIC,HPG,VCB)
        min_gti_score: Điểm GTI tối thiểu
        min_combined_score: Điểm tổng hợp tối thiểu
    
    Returns:
        Kết quả scan cho danh sách tùy chỉnh
    """
    try:
        # Parse stock list
        stock_list = [stock.strip().upper() for stock in stocks.split(",") if stock.strip()]
        
        if not stock_list:
            raise HTTPException(status_code=400, detail="Danh sách mã cổ phiếu không được để trống")
        
        if len(stock_list) > 50:
            raise HTTPException(status_code=400, detail="Tối đa 50 mã cổ phiếu trong một lần scan")
        
        print(f"🎯 Custom scan cho {len(stock_list)} mã: {stock_list}")
        
        # Thực hiện scan
        scan_result = market_scan_parallel(
            stock_list=stock_list,
            min_gti_score=min_gti_score,
            min_combined_score=min_combined_score,
            max_workers=GTIConfig.MARKET_SCAN_BATCH_SIZE,
            timeout=GTIConfig.MARKET_SCAN_TIMEOUT
        )
        
        results = scan_result["scan_results"]
        
        return {
            "custom_scan_results": {
                "input_stocks": stock_list,
                "qualified_stocks": results,
                "scan_summary": {
                    "input_count": len(stock_list),
                    "qualified_count": len(results),
                    "success_rate": f"{scan_result['statistics']['success_count']}/{len(stock_list)}",
                    "qualification_rate": f"{len(results)}/{len(stock_list)}"
                }
            },
            "performance_ranking": {
                "top_3": results[:3] if len(results) >= 3 else results,
                "worst_qualified": results[-1] if results else None
            },
            "execution_statistics": scan_result["statistics"],
            "errors": scan_result["errors"] if scan_result["errors"] else None,
            "scan_timestamp": scan_result["scan_timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi custom scan: {str(e)}")

@app.get("/market-scan/quick-check/{stock}")
def quick_check_single_stock(stock: str):
    """
    ⚡ QUICK CHECK - Kiểm tra nhanh một mã có đạt tiêu chí GTI không
    
    Args:
        stock: Mã cổ phiếu cần kiểm tra
    
    Returns:
        Kết quả nhanh với điểm số và đánh giá
    """
    try:
        result = scan_single_stock(
            stock_symbol=stock.upper(),
            min_gti_score=0,  # Không lọc để luôn có kết quả
            min_combined_score=-10  # Để luôn trả về kết quả
        )
        
        if result is None:
            # Nếu không có kết quả, thử lấy dữ liệu cơ bản
            try:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                
                df = lay_du_lieu_co_phieu_vnstock(stock.upper(), start_date, end_date)
                if df is None or df.empty:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy dữ liệu cho mã {stock}")
                
                df_analyzed = tinh_toan_chi_bao_ky_thuat(df)
                latest = df_analyzed.iloc[-1]
                gti_score = int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0
                
                return {
                    "stock_symbol": stock.upper(),
                    "current_price": round(float(latest['close']), 2),
                    "gti_score": gti_score,
                    "quick_evaluation": "Không đạt tiêu chí GTI cơ bản" if gti_score < 2 else "Có tiềm năng",
                    "recommendation": "AVOID" if gti_score < 2 else "WATCH",
                    "note": "Chưa có pattern analysis đầy đủ"
                }
                
            except Exception:
                raise HTTPException(status_code=404, detail=f"Không thể lấy dữ liệu cho mã {stock}")
        
        return {
            "quick_check_result": {
                "stock_symbol": result["stock_symbol"],
                "current_price": result["current_price"],
                "scores": {
                    "gti_score": result["gti_score"],
                    "pattern_score": result["pattern_score"]["net"],
                    "combined_score": result["combined_score"]
                },
                "evaluation": result["evaluation"],
                "key_signals": {
                    "trend_ok": result["key_metrics"]["gti_trend_check"],
                    "recent_breakout": result["key_metrics"]["gti_recent_breakout"],
                    "good_pullback": result["key_metrics"]["gti_is_pullback"],
                    "near_high": result["key_metrics"]["gti_dist_to_high_percent"] is not None and result["key_metrics"]["gti_dist_to_high_percent"] <= 15
                }
            },
            "quick_summary": f"GTI: {result['gti_score']}/4, Pattern: {result['pattern_score']['bullish']}B/{result['pattern_score']['bearish']}Be, Tổng: {result['combined_score']}",
            "current_patterns": result["current_patterns"],
            "check_timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi quick check: {str(e)}")

# 🚀 CACHE MANAGEMENT ENDPOINTS

@app.get("/cache/stats")
def get_cache_stats():
    """
    📊 CACHE STATS - Xem thống kê performance của cache
    
    Returns:
        Thống kê chi tiết về cache usage và performance
    """
    try:
        stats = gti_cache.get_stats()
        
        return {
            "cache_statistics": stats,
            "performance_info": {
                "cache_enabled": stats.get("cache_enabled", False),
                "hit_rate": f"{stats.get('total_hits', 0)} hits total",
                "efficiency": "Good" if stats.get('total_hits', 0) > stats.get('valid_entries', 1) else "Low",
                "memory_usage": stats.get("memory_usage_estimate", "N/A")
            },
            "recommendations": {
                "cache_working": stats.get("cache_enabled", False),
                "entries_count": stats.get("total_entries", 0),
                "expired_cleanup_needed": stats.get("expired_entries", 0) > 10
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Lỗi lấy cache stats: {str(e)}"}

@app.post("/cache/clear")
def clear_cache(operation: Optional[str] = None):
    """
    🗑️ CACHE CLEAR - Xóa cache để refresh dữ liệu
    
    Args:
        operation: Loại operation cần xóa (None = xóa tất cả)
    
    Returns:
        Confirmation và stats mới
    """
    try:
        old_stats = gti_cache.get_stats()
        old_count = old_stats.get("total_entries", 0)
        
        if operation:
            gti_cache.invalidate(operation)
            message = f"Cache cleared for operation: {operation}"
        else:
            gti_cache.invalidate()
            message = "All cache cleared"
        
        new_stats = gti_cache.get_stats()
        new_count = new_stats.get("total_entries", 0)
        
        return {
            "cache_clear_result": {
                "message": message,
                "entries_before": old_count,
                "entries_after": new_count,
                "entries_removed": old_count - new_count
            },
            "current_stats": new_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Lỗi clear cache: {str(e)}"}

@app.get("/system/performance")
def get_system_performance():
    """
    ⚡ SYSTEM PERFORMANCE - Tổng quan performance của hệ thống
    
    Returns:
        Thông tin performance tổng hợp
    """
    try:
        cache_stats = gti_cache.get_stats()
        
        return {
            "system_performance": {
                "cache_system": {
                    "enabled": cache_stats.get("cache_enabled", False),
                    "total_entries": cache_stats.get("total_entries", 0),
                    "hit_count": cache_stats.get("total_hits", 0),
                    "memory_usage": cache_stats.get("memory_usage_estimate", "N/A")
                },
                "optimization_settings": {
                    "market_scan_timeout": f"{GTIConfig.MARKET_SCAN_TIMEOUT}s",
                    "batch_size": GTIConfig.MARKET_SCAN_BATCH_SIZE,
                    "single_stock_timeout": f"{GTIConfig.SINGLE_STOCK_TIMEOUT}s",
                    "chunk_size": GTIConfig.CHUNK_SIZE_FOR_LARGE_SCANS,
                    "progressive_timeout": GTIConfig.ENABLE_PROGRESSIVE_TIMEOUT,
                    "quick_mode": GTIConfig.TOP_PICKS_QUICK_MODE
                },
                "performance_features": [
                    "✅ Chunked processing for large scans",
                    "✅ Progressive timeout scaling",
                    "✅ In-memory caching system", 
                    "✅ Optimized worker pool",
                    "✅ Quick mode for top picks",
                    "✅ Individual stock result caching"
                ]
            },
            "recommendations": {
                "use_cache": "Enable caching for repeated requests",
                "use_quick_mode": "Use quick mode for faster top picks",
                "batch_requests": "Combine multiple stock checks into custom scans",
                "limit_results": "Use limit parameter for faster responses"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Lỗi system performance: {str(e)}"}

# 🔄 ASYNCHRONOUS MARKET SCANNING ENDPOINTS
# These endpoints implement the asynchronous processing pattern from upgrade.md

@app.post("/market-scan/start")
def start_market_scan_task(
    task_type: str,
    category: Optional[str] = None,
    sector: Optional[str] = None,
    stocks: Optional[str] = None,
    limit: Optional[int] = None,
    min_gti_score: int = 2,
    min_combined_score: int = 3
):
    """
    🚀 START ASYNC TASK - Bắt đầu tác vụ quét thị trường bất đồng bộ
    
    Args:
        task_type: Loại task (top_picks, sector_scan, category_scan, custom_scan)
        category: Danh mục cho category_scan (vn30, popular, etc.)
        sector: Ngành cho sector_scan (banking, technology, etc.)
        stocks: Danh sách mã cho custom_scan (VD: FPT,VIC,HPG)
        limit: Giới hạn kết quả cho top_picks
        min_gti_score: Điểm GTI tối thiểu (0-4)
        min_combined_score: Điểm tổng hợp tối thiểu
    
    Returns:
        task_id để theo dõi tiến trình
        
    Example requests:
        POST /market-scan/start?task_type=top_picks&limit=15
        POST /market-scan/start?task_type=sector_scan&sector=banking
        POST /market-scan/start?task_type=category_scan&category=vn30
        POST /market-scan/start?task_type=custom_scan&stocks=FPT,VIC,HPG,VCB
    """
    try:
        # Validate task_type
        valid_task_types = ["top_picks", "sector_scan", "category_scan", "custom_scan"]
        if task_type not in valid_task_types:
            raise HTTPException(
                status_code=400, 
                detail=f"task_type không hợp lệ. Các loại hỗ trợ: {valid_task_types}"
            )
        
        # Prepare parameters based on task type
        parameters = {
            "min_gti_score": min_gti_score,
            "min_combined_score": min_combined_score
        }
        
        if task_type == "top_picks":
            parameters["limit"] = limit or 15
            
        elif task_type == "sector_scan":
            if not sector:
                raise HTTPException(status_code=400, detail="sector là bắt buộc cho sector_scan")
            available_sectors = list(GTIConfig.SECTOR_STOCKS.keys())
            if sector.lower() not in available_sectors:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ngành '{sector}' không hợp lệ. Các ngành có sẵn: {available_sectors}"
                )
            parameters["sector"] = sector.lower()
            
        elif task_type == "category_scan":
            if not category:
                raise HTTPException(status_code=400, detail="category là bắt buộc cho category_scan")
            parameters["category"] = category.lower()
            
        elif task_type == "custom_scan":
            if not stocks:
                raise HTTPException(status_code=400, detail="stocks là bắt buộc cho custom_scan")
            stock_list = [s.strip().upper() for s in stocks.split(",") if s.strip()]
            if len(stock_list) > 50:
                raise HTTPException(status_code=400, detail="Tối đa 50 mã cổ phiếu trong một lần scan")
            parameters["stocks"] = stocks
        
        # Create and start task
        task_id = task_manager.create_task(task_type, parameters)
        
        return {
            "status": "processing_started",
            "task_id": task_id,
            "task_type": task_type,
            "parameters": parameters,
            "message": "Tác vụ đã được bắt đầu. Sử dụng task_id để kiểm tra tiến trình.",
            "next_steps": {
                "check_status": f"GET /market-scan/status/{task_id}",
                "get_result": f"GET /market-scan/result/{task_id}"
            },
            "estimated_time": {
                "top_picks": "2-5 phút",
                "sector_scan": "1-3 phút", 
                "category_scan": "30s-2 phút",
                "custom_scan": "10s-2 phút tùy số lượng mã"
            }.get(task_type, "1-5 phút"),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khởi tạo task: {str(e)}")

@app.get("/market-scan/status/{task_id}")
def get_market_scan_status(task_id: str):
    """
    🔍 CHECK STATUS - Kiểm tra trạng thái tác vụ bất đồng bộ
    
    Args:
        task_id: ID của task cần kiểm tra
    
    Returns:
        Thông tin trạng thái hiện tại của task
        
    Possible statuses:
        - pending: Đang chờ xử lý
        - running: Đang thực hiện 
        - completed: Hoàn thành (có thể lấy kết quả)
        - failed: Thất bại (có thông tin lỗi)
        - expired: Đã hết hạn (>1 tiếng)
    """
    try:
        status = task_manager.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy task với ID: {task_id}")
        
        response = {
            "task_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add appropriate next action based on status
        if status["status"] == "running":
            response["message"] = "Tác vụ đang chạy, vui lòng đợi..."
            response["action"] = "Kiểm tra lại sau 10-30 giây"
            
        elif status["status"] == "completed":
            response["message"] = "Tác vụ hoàn thành! Có thể lấy kết quả."
            response["action"] = f"GET /market-scan/result/{task_id}"
            
        elif status["status"] == "failed":
            response["message"] = "Tác vụ thất bại."
            response["action"] = "Kiểm tra lỗi và thử tạo task mới"
            
        elif status["status"] == "expired":
            response["message"] = "Tác vụ đã hết hạn."
            response["action"] = "Tạo task mới để thực hiện"
            
        else:  # pending
            response["message"] = "Tác vụ đang chờ xử lý..."
            response["action"] = "Kiểm tra lại trong vài giây"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kiểm tra status: {str(e)}")

@app.get("/market-scan/result/{task_id}")
def get_market_scan_result(task_id: str):
    """
    📊 GET RESULT - Lấy kết quả của tác vụ đã hoàn thành
    
    Args:
        task_id: ID của task cần lấy kết quả
    
    Returns:
        Kết quả phân tích đầy đủ từ task đã hoàn thành
        
    Note:
        - Chỉ có thể lấy kết quả khi status = "completed"
        - Kết quả sẽ bị xóa sau 1 tiếng để tiết kiệm bộ nhớ
    """
    try:
        # First check status
        status = task_manager.get_task_status(task_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy task với ID: {task_id}")
        
        if status["status"] != "completed":
            current_status = status["status"]
            if current_status == "running":
                raise HTTPException(status_code=202, detail="Tác vụ vẫn đang chạy. Vui lòng đợi.")
            elif current_status == "failed":
                raise HTTPException(status_code=400, detail=f"Tác vụ thất bại: {status.get('error', 'Unknown error')}")
            elif current_status == "expired":
                raise HTTPException(status_code=410, detail="Tác vụ đã hết hạn. Vui lòng tạo task mới.")
            else:
                raise HTTPException(status_code=202, detail=f"Tác vụ chưa hoàn thành. Status: {current_status}")
        
        # Get result
        result = task_manager.get_task_result(task_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Không tìm thấy kết quả cho task này.")
        
        # Format response with metadata
        response = {
            "task_info": {
                "task_id": task_id,
                "task_type": result["task_type"],
                "parameters": result["parameters"],
                "execution_time": result.get("execution_time"),
                "completed_at": status["completed_at"]
            },
            "scan_results": result["scan_result"],
            "result_summary": {
                "success": True,
                "data_available": True,
                "result_type": result["task_type"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add task-specific formatting
        if result["task_type"] == "top_picks":
            if "top_picks" in result["scan_result"]:
                response["formatted_results"] = {
                    "market_overview": "Top picks scan completed successfully",
                    "top_recommendations": result["scan_result"].get("top_picks", [])[:5],
                    "total_qualified": len(result["scan_result"].get("top_picks", [])),
                    "recommendation": result["scan_result"].get("recommendation", {})
                }
        
        elif result["task_type"] in ["sector_scan", "category_scan"]:
            if "scan_results" in result["scan_result"]:
                qualified_stocks = result["scan_result"]["scan_results"]
                response["formatted_results"] = {
                    "scan_overview": f"{result['task_type']} completed successfully",
                    "qualified_stocks": qualified_stocks,
                    "total_qualified": len(qualified_stocks),
                    "top_3_picks": qualified_stocks[:3] if len(qualified_stocks) >= 3 else qualified_stocks
                }
        
        elif result["task_type"] == "custom_scan":
            if "scan_results" in result["scan_result"]:
                qualified_stocks = result["scan_result"]["scan_results"]
                response["formatted_results"] = {
                    "scan_overview": "Custom scan completed successfully",
                    "input_stocks": result["parameters"]["stocks"].split(","),
                    "qualified_stocks": qualified_stocks,
                    "qualification_rate": f"{len(qualified_stocks)}/{len(result['parameters']['stocks'].split(','))}"
                }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy kết quả: {str(e)}")

# 📊 TASK MANAGEMENT ENDPOINTS

@app.get("/tasks/stats")
def get_task_manager_stats():
    """
    📊 TASK STATS - Xem thống kê của task manager
    
    Returns:
        Thống kê về các task đang chạy và đã hoàn thành
    """
    try:
        stats = task_manager.get_stats()
        
        return {
            "task_manager_stats": stats,
            "system_info": {
                "async_processing": "Active",
                "background_workers": stats["executor_info"]["max_workers"],
                "total_tasks_handled": stats["total_tasks"]
            },
            "recommendations": {
                "optimal_usage": "Sử dụng async endpoints cho scan lớn (>20 mã)",
                "check_interval": "Kiểm tra status mỗi 15-30 giây",
                "task_cleanup": "Tasks tự động cleanup sau 1 tiếng"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Lỗi lấy task stats: {str(e)}"}