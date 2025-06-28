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
    prepare_news_search_context
)

# Khởi tạo ứng dụng FastAPI
app = FastAPI(
    title="🚀 GTI Stock Analysis API",
    description="API phân tích chứng khoán Việt Nam với hệ thống GTI (Growth Trading Intelligence) + Pattern Detection miễn phí",
    version="3.0.0",
    contact={
        "name": "GTI Analysis System",
        "url": "https://github.com/your-username/stock-gti-analysis",
    },
)

@app.get("/")
def read_root():
    return {
        "message": "🚀 Chào mừng đến với GTI Stock Analysis API!",
        "he_thong": "GTI PRO v2.0 - Growth Trading Intelligence + Enhanced Pattern Detection",
        "phien_ban": "3.2.0",
        "tinh_nang": [
            "🔥 GTI Core Analysis (4 tiêu chí cốt lõi)",
            "🎯 Enhanced Pattern Detection (16 patterns: 12 basic + 4 large)",
            "🌊 Market Context Analysis (VNINDEX + Sector)",
            "📰 News Search Integration (cho ChatGPT)",
            "⚡ Combined Scoring (-5 to +18 range)",
            "🚀 Comprehensive Analysis API"
        ],
        "endpoints": {
            "/phan-tich/{ma_co_phieu}": "Phân tích GTI cơ bản",
            "/full-analysis/{ma_co_phieu}": "🚀 GTI PRO v2.0 - Phân tích toàn diện",
            "/full-analysis-legacy/{ma_co_phieu}": "Phân tích đầy đủ GTI + Patterns (legacy)",
            "/news-context/{ma_co_phieu}": "News search context cho ChatGPT",
            "/gti-info": "Thông tin về hệ thống GTI",
            "/patterns-info": "Thông tin về 16 patterns (12 basic + 4 large)"
        },
        "vi_du": "/full-analysis/FPT"
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
        
        # Tính điểm tổng hợp
        gti_score = int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0
        bullish_score = int(pattern_results.get('bullish_score', 0))
        bearish_score = int(pattern_results.get('bearish_score', 0))
        tong_diem = gti_score + bullish_score - bearish_score
        
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