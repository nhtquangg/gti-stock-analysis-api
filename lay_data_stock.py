# Nhập các thư viện cần thiết
try:
    from vnstock import Vnstock
    print("Đã import thành công thư viện vnstock")
except ImportError:
    print("Chưa cài đặt thư viện vnstock. Vui lòng chạy: pip install vnstock")
    import sys
    sys.exit(1)

try:
    import ta
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    print("Đã import thành công thư viện ta, pandas, numpy và datetime")
except ImportError:
    print("Chưa cài đặt thư viện ta, pandas hoặc numpy. Vui lòng chạy: pip install ta pandas numpy")
    import sys
    sys.exit(1)

import concurrent.futures
import time
from config import GTIConfig
from rate_limiter import rate_limited_call, rate_limiter

def lay_du_lieu_co_phieu_vnstock(ma_co_phieu: str, start_date: str = "2023-01-01", end_date: str = "2024-12-31"):
    """
    Hàm này lấy dữ liệu giá lịch sử của một mã cổ phiếu sử dụng thư viện vnstock 3.x.
    🛡️ PROTECTED BY RATE LIMITER
    
    Args:
        ma_co_phieu (str): Mã chứng khoán cần lấy, ví dụ: "FPT", "HPG".
        start_date (str): Ngày bắt đầu, định dạng YYYY-MM-DD
        end_date (str): Ngày kết thúc, định dạng YYYY-MM-DD

    Returns:
        DataFrame chứa dữ liệu lịch sử nếu thành công, hoặc None nếu có lỗi.
    """
    print(f"Bắt đầu lấy dữ liệu cho mã: {ma_co_phieu} từ vnstock")
    print(f"Thời gian: từ {start_date} đến {end_date}")
    
    def _vnstock_api_call():
        """Internal function để gọi vnstock API"""
        stock = Vnstock().stock(symbol=ma_co_phieu, source='VCI')
        return stock.quote.history(start=start_date, end=end_date, interval='1D')
    
    try:
        # 🛡️ Sử dụng rate-limited call để bảo vệ API
        df = rate_limited_call(_vnstock_api_call)
        
        if df is not None and not df.empty:
            print("Lấy dữ liệu thành công!")
            return df
        else:
            print(f"Không có dữ liệu cho mã {ma_co_phieu} trong khoảng thời gian yêu cầu.")
            return None
            
    except Exception as e:
        error_str = str(e).lower()
        if "rate" in error_str or "limit" in error_str or "quota" in error_str:
            print(f"🛡️ Rate limit đã được xử lý bởi rate limiter: {e}")
        else:
            print(f"Lỗi khi lấy dữ liệu: {e}")
        print("Có thể thử lại sau hoặc kiểm tra lại mã cổ phiếu")
        return None

def tinh_toan_chi_bao_ky_thuat(df: pd.DataFrame):
    """
    Hàm này nhận vào một DataFrame và tính toán các chỉ báo kỹ thuật theo hệ thống GTI.
    """
    print("\nBắt đầu tính toán các chỉ báo kỹ thuật theo hệ thống GTI...")
    
    # Tạo bản sao để tránh thay đổi dữ liệu gốc
    df = df.copy()
    
    # 1. Các đường EMA theo hệ thống GTI
    df['EMA10'] = ta.trend.EMAIndicator(df['close'], window=10).ema_indicator()
    df['EMA20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['EMA50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['EMA200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
    
    # 2. Tính toán khối lượng trung bình 20 phiên
    df['volume_avg_20'] = df['volume'].rolling(window=20).mean()
    
    # 3. Tính toán đỉnh 1 năm (252 phiên giao dịch)
    df['high_1_year'] = df['high'].rolling(window=252, min_periods=1).max()
    
    # 4. GTI Trend Check: EMA10 > EMA20 và price > EMA10 > EMA20
    df['gti_trend_check'] = (
        (df['EMA10'] > df['EMA20']) & 
        (df['close'] > df['EMA10']) & 
        (df['close'] > df['EMA20'])
    )
    
    # 5. GTI Recent Breakout: Volume > 1.5x trung bình và giá tăng mạnh
    # Kiểm tra trong 5 phiên gần nhất có breakout không
    df['volume_breakout'] = df['volume'] > (df['volume_avg_20'] * 1.5)
    df['price_increase'] = (df['close'] - df['close'].shift(1)) / df['close'].shift(1) > 0.03  # Tăng > 3%
    df['daily_breakout'] = df['volume_breakout'] & df['price_increase']
    df['gti_recent_breakout'] = df['daily_breakout'].rolling(window=5).max().fillna(False).astype(bool)
    
    # 6. GTI Distance to High: Khoảng cách đến đỉnh 1 năm (%)
    df['gti_dist_to_high_percent'] = ((df['high_1_year'] - df['close']) / df['close'] * 100).round(2)
    
    # 7. GTI Pullback Check: Giá gần EMA10 hoặc EMA20 (trong vòng 2%)
    df['distance_to_ema10_percent'] = abs((df['close'] - df['EMA10']) / df['EMA10'] * 100)
    df['distance_to_ema20_percent'] = abs((df['close'] - df['EMA20']) / df['EMA20'] * 100)
    df['gti_is_pullback'] = (
        (df['distance_to_ema10_percent'] <= 2.0) | 
        (df['distance_to_ema20_percent'] <= 2.0)
    )
    
    # 8. Các chỉ báo kỹ thuật truyền thống (giữ lại cho tham khảo)
    df['RSI'] = ta.momentum.RSIIndicator(df['close']).rsi()
    macd = ta.trend.MACD(df['close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['SMA_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
    
    # 9. GTI Overall Score: Tổng điểm GTI (0-4)
    df['gti_score'] = (
        df['gti_trend_check'].astype(int) +
        df['gti_recent_breakout'].astype(int) +
        (df['gti_dist_to_high_percent'] <= 15).astype(int) +  # Gần đỉnh (cách < 15%)
        df['gti_is_pullback'].astype(int)
    )
    
    # 10. GTI Signal: Tín hiệu mua/bán theo GTI
    df['gti_signal'] = 'HOLD'
    df.loc[df['gti_score'] >= 3, 'gti_signal'] = 'BUY'
    df.loc[df['gti_score'] <= 1, 'gti_signal'] = 'AVOID'
    
    print("Tính toán các chỉ báo GTI hoàn tất!")
    return df

def detect_free_patterns(df: pd.DataFrame):
    """
    Hàm miễn phí để detect các patterns phổ biến - không cần thư viện trả phí
    Hoàn toàn tự code dựa trên logic OHLC
    """
    print("\nBắt đầu phát hiện patterns miễn phí...")
    
    # Tạo bản sao
    df = df.copy()
    
    # Tính toán các giá trị cơ bản
    df['body_size'] = abs(df['close'] - df['open'])
    df['total_range'] = df['high'] - df['low']
    df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    
    # 1. DOJI PATTERN (nến doji - open ≈ close)
    df['pattern_doji'] = (df['body_size'] / df['total_range']) < 0.1
    
    # 2. HAMMER PATTERN (nến búa - shadow dưới dài)
    df['pattern_hammer'] = (
        (df['lower_shadow'] > 2 * df['body_size']) & 
        (df['upper_shadow'] < df['body_size']) &
        (df['total_range'] > 0)  # Tránh chia cho 0
    )
    
    # 3. HANGING MAN (nến treo cổ - giống hammer nhưng ở đỉnh)
    df['pattern_hanging_man'] = (
        df['pattern_hammer'] & 
        (df['close'] < df['close'].shift(1))  # Giá giảm so với phiên trước
    )
    
    # 4. BULLISH ENGULFING (nến bao phủ tăng)
    prev_bearish = df['is_bearish'].shift(1)
    curr_bullish = df['is_bullish']
    engulfs = (df['open'] <= df['close'].shift(1)) & (df['close'] >= df['open'].shift(1))
    df['pattern_bullish_engulfing'] = prev_bearish & curr_bullish & engulfs
    
    # 5. BEARISH ENGULFING (nến bao phủ giảm)
    prev_bullish = df['is_bullish'].shift(1)
    curr_bearish = df['is_bearish']
    engulfs_bear = (df['open'] >= df['close'].shift(1)) & (df['close'] <= df['open'].shift(1))
    df['pattern_bearish_engulfing'] = prev_bullish & curr_bearish & engulfs_bear
    
    # 6. MORNING STAR (sao mai - 3 nến)
    # Nến 1: bearish, Nến 2: doji/small body, Nến 3: bullish
    cond1 = df['is_bearish'].shift(2)  # Nến 1 giảm
    cond2 = (df['body_size'].shift(1) / df['total_range'].shift(1)) < 0.3  # Nến 2 thân nhỏ
    cond3 = df['is_bullish']  # Nến 3 tăng
    cond4 = df['close'] > df['close'].shift(2)  # Nến 3 cao hơn nến 1
    df['pattern_morning_star'] = cond1 & cond2 & cond3 & cond4
    
    # 7. EVENING STAR (sao hôm - 3 nến)
    cond1_eve = df['is_bullish'].shift(2)  # Nến 1 tăng
    cond2_eve = (df['body_size'].shift(1) / df['total_range'].shift(1)) < 0.3  # Nến 2 thân nhỏ
    cond3_eve = df['is_bearish']  # Nến 3 giảm
    cond4_eve = df['close'] < df['close'].shift(2)  # Nến 3 thấp hơn nến 1
    df['pattern_evening_star'] = cond1_eve & cond2_eve & cond3_eve & cond4_eve
    
    # 8. SUPPORT/RESISTANCE LEVELS (đơn giản)
    window = 20
    df['resistance_level'] = df['high'].rolling(window=window).max().shift(1)
    df['support_level'] = df['low'].rolling(window=window).min().shift(1)
    
    # 9. BREAKOUT PATTERNS
    df['pattern_resistance_breakout'] = (
        (df['close'] > df['resistance_level']) & 
        (df['volume'] > df['volume'].rolling(window=20).mean() * 1.2)  # Volume cao
    )
    
    df['pattern_support_breakdown'] = (
        (df['close'] < df['support_level']) & 
        (df['volume'] > df['volume'].rolling(window=20).mean() * 1.2)  # Volume cao
    )
    
    # 10. VOLUME SPIKE PATTERN
    df['volume_avg_20'] = df['volume'].rolling(window=20).mean()
    df['pattern_volume_spike'] = df['volume'] > (df['volume_avg_20'] * 2)
    
    # 11. GAP PATTERNS
    df['gap_up'] = df['low'] > df['high'].shift(1)
    df['gap_down'] = df['high'] < df['low'].shift(1)
    df['pattern_gap_up'] = df['gap_up'] & df['is_bullish']
    df['pattern_gap_down'] = df['gap_down'] & df['is_bearish']
    
    # 12. SIMPLE TREND PATTERNS
    df['trend_5d'] = df['close'].rolling(5).apply(lambda x: 1 if x.iloc[-1] > x.iloc[0] else 0)
    df['pattern_strong_uptrend'] = (
        (df['trend_5d'] == 1) & 
        (df['close'] > df['close'].rolling(10).mean()) &
        (df['volume'] > df['volume_avg_20'])
    )
    
    print("Phát hiện patterns miễn phí hoàn tất!")
    return df

def phan_tich_pattern_results(df: pd.DataFrame, ma_co_phieu: str):
    """
    Phân tích kết quả patterns và đưa ra báo cáo
    """
    print(f"\n📊 BÁO CÁO PATTERNS CHO MÃ {ma_co_phieu}")
    print("="*50)
    
    # Lấy dữ liệu 10 phiên gần nhất
    recent_data = df.tail(10)
    latest = df.iloc[-1]
    
    # Đếm patterns trong 10 phiên gần nhất
    pattern_columns = [col for col in df.columns if col.startswith('pattern_')]
    
    print("🔍 PATTERNS PHÁT HIỆN TRONG 10 PHIÊN GẦN NHẤT:")
    for pattern in pattern_columns:
        count = recent_data[pattern].sum()
        if count > 0:
            pattern_name = pattern.replace('pattern_', '').replace('_', ' ').title()
            print(f"   ✅ {pattern_name}: {count} lần")
    
    print(f"\n📈 THÔNG TIN PHIÊN GẦN NHẤT ({latest.name}):")
    print(f"   Giá đóng cửa: {latest['close']:,.0f} VND")
    print(f"   Khối lượng: {latest['volume']:,.0f}")
    print(f"   Support level: {latest['support_level']:,.0f} VND")
    print(f"   Resistance level: {latest['resistance_level']:,.0f} VND")
    
    print(f"\n🎯 PATTERNS HIỆN TẠI:")
    current_patterns = []
    for pattern in pattern_columns:
        if latest[pattern]:
            pattern_name = pattern.replace('pattern_', '').replace('_', ' ').title()
            current_patterns.append(pattern_name)
    
    if current_patterns:
        for p in current_patterns:
            print(f"   🔥 {p}")
    else:
        print("   ➡️  Không có pattern đặc biệt")
    
    # Tính điểm pattern tổng hợp (bao gồm cả large patterns)
    bullish_patterns = ['bullish_engulfing', 'morning_star', 'hammer', 'resistance_breakout', 'gap_up', 'strong_uptrend']
    bearish_patterns = ['bearish_engulfing', 'evening_star', 'hanging_man', 'support_breakdown', 'gap_down']
    
    # Thêm large patterns (có điểm cao hơn do quan trọng hơn)
    large_bullish_patterns = ['cup_handle', 'bull_flag', 'base_n_break', 'ascending_triangle']
    
    # Điểm cho patterns thường
    bullish_score = sum([latest[f'pattern_{p}'] for p in bullish_patterns if f'pattern_{p}' in df.columns])
    bearish_score = sum([latest[f'pattern_{p}'] for p in bearish_patterns if f'pattern_{p}' in df.columns])
    
    # Điểm cho large patterns (x2 do quan trọng hơn)
    large_bullish_score = sum([latest[f'pattern_{p}'] * 2 for p in large_bullish_patterns if f'pattern_{p}' in df.columns])
    
    # Tổng điểm bullish
    bullish_score += large_bullish_score
    
    print(f"\n⚖️  ĐIỂM PATTERN TỔNG HỢP:")
    print(f"   Bullish Score: {bullish_score}")
    print(f"   Bearish Score: {bearish_score}")
    
    if bullish_score > bearish_score:
        print(f"   📈 Xu hướng: TÍCH CỰC")
    elif bearish_score > bullish_score:
        print(f"   📉 Xu hướng: TIÊU CỰC") 
    else:
        print(f"   ➡️  Xu hướng: TRUNG TÍNH")
    
    # ✅ GIẢI PHÁP: Ép kiểu về int tiêu chuẩn của Python trước khi trả về
    return {
        'bullish_score': int(bullish_score),
        'bearish_score': int(bearish_score),
        'current_patterns': current_patterns,
        'latest_data': latest
    }

def detect_large_chart_patterns(df: pd.DataFrame, lookback_window: int = 60):
    """
    🔍 Phát hiện các mẫu hình lớn (Large Chart Patterns)
    - Cup & Handle
    - Bull Flag / Bear Flag  
    - Base n' Break
    - Ascending/Descending Triangle
    """
    print("\n🔍 Bắt đầu phát hiện mẫu hình lớn...")
    
    df = df.copy()
    
    # Tính toán rolling max/min cho pattern detection
    df['rolling_high_20'] = df['high'].rolling(window=20).max()
    df['rolling_low_20'] = df['low'].rolling(window=20).min()
    df['rolling_high_60'] = df['high'].rolling(window=60).max()
    df['rolling_low_60'] = df['low'].rolling(window=60).min()
    
    # 1. CUP & HANDLE PATTERN
    def detect_cup_and_handle(df_local, window=50):
        """Phát hiện mẫu hình Cup & Handle"""
        patterns = []
        
        for i in range(window, len(df_local) - 10):
            # Lấy dữ liệu trong window
            data_window = df_local.iloc[i-window:i+10]
            
            # Tìm 2 đỉnh cao nhất (left rim, right rim)
            high_peaks = data_window['high'].nlargest(3)
            
            if len(high_peaks) >= 2:
                # Cup: có đáy sâu giữa 2 đỉnh
                left_peak = high_peaks.iloc[0]
                right_peak = high_peaks.iloc[1]
                
                # Cup depth should be 12-33% of left peak
                cup_depth_ratio = (left_peak - data_window['low'].min()) / left_peak
                
                if 0.12 <= cup_depth_ratio <= 0.33:
                    # Handle: pullback < 50% of cup depth
                    handle_start = i
                    recent_data = df_local.iloc[handle_start:handle_start+10]
                    
                    if len(recent_data) > 5:
                        handle_depth = (recent_data['high'].max() - recent_data['low'].min()) / recent_data['high'].max()
                        
                        if handle_depth < (cup_depth_ratio * 0.5):
                            patterns.append(i)
        
        return patterns
    
    cup_handle_patterns = detect_cup_and_handle(df)
    df['pattern_cup_handle'] = False
    if cup_handle_patterns:
        for idx in cup_handle_patterns:
            if idx < len(df):
                df.iloc[idx, df.columns.get_loc('pattern_cup_handle')] = True
    
    # 2. BULL FLAG PATTERN
    def detect_bull_flag(df_local, window=30):
        """Phát hiện mẫu hình Bull Flag"""
        patterns = []
        
        for i in range(window, len(df_local) - 5):
            # Flagpole: Strong upward move
            flagpole_data = df_local.iloc[i-window:i-10]
            recent_data = df_local.iloc[i-10:i]
            
            # Check for strong upward move (flagpole)
            flagpole_gain = (flagpole_data['close'].iloc[-1] - flagpole_data['close'].iloc[0]) / flagpole_data['close'].iloc[0]
            
            if flagpole_gain > 0.15:  # At least 15% gain
                # Flag: slight downward or sideways consolidation
                flag_slope = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / len(recent_data)
                flag_range = (recent_data['high'].max() - recent_data['low'].min()) / recent_data['close'].mean()
                
                # Flag should be small consolidation
                if -0.08 <= flag_slope <= 0.03 and flag_range < 0.15:
                    # Volume should decrease during flag
                    volume_trend = recent_data['volume'].iloc[-3:].mean() < flagpole_data['volume'].iloc[-3:].mean()
                    if volume_trend:
                        patterns.append(i)
        
        return patterns
    
    bull_flag_patterns = detect_bull_flag(df)
    df['pattern_bull_flag'] = False
    if bull_flag_patterns:
        for idx in bull_flag_patterns:
            if idx < len(df):
                df.iloc[idx, df.columns.get_loc('pattern_bull_flag')] = True
    
    # 3. BASE N' BREAK PATTERN
    def detect_base_n_break(df_local, window=40):
        """Phát hiện mẫu hình Base n' Break"""
        patterns = []
        
        for i in range(window, len(df_local) - 3):
            base_data = df_local.iloc[i-window:i]
            
            # Base: tight sideways consolidation
            base_range = (base_data['high'].max() - base_data['low'].min()) / base_data['close'].mean()
            
            # Base should be tight (< 20% range)
            if base_range < 0.20:
                # Check for decreasing volatility in base
                early_base = base_data.iloc[:len(base_data)//2]
                late_base = base_data.iloc[len(base_data)//2:]
                
                early_volatility = (early_base['high'] - early_base['low']).mean() / early_base['close'].mean()
                late_volatility = (late_base['high'] - late_base['low']).mean() / late_base['close'].mean()
                
                # Volatility contraction
                if late_volatility < early_volatility:
                    # Breakout: price breaks above base resistance with volume
                    resistance_level = base_data['high'].max()
                    current_price = df_local.iloc[i]['close']
                    current_volume = df_local.iloc[i]['volume']
                    avg_volume = base_data['volume'].mean()
                    
                    if current_price > resistance_level and current_volume > (avg_volume * 1.5):
                        patterns.append(i)
        
        return patterns
    
    base_break_patterns = detect_base_n_break(df)
    df['pattern_base_n_break'] = False
    if base_break_patterns:
        for idx in base_break_patterns:
            if idx < len(df):
                df.iloc[idx, df.columns.get_loc('pattern_base_n_break')] = True
    
    # 4. ASCENDING TRIANGLE
    def detect_ascending_triangle(df_local, window=30):
        """Phát hiện mẫu hình Ascending Triangle"""
        patterns = []
        
        for i in range(window, len(df_local) - 5):
            triangle_data = df_local.iloc[i-window:i]
            
            # Resistance: horizontal line (multiple touches at same level)
            resistance_level = triangle_data['high'].max()
            resistance_touches = len(triangle_data[triangle_data['high'] >= resistance_level * 0.99])
            
            # Support: rising trend line
            lows = triangle_data['low']
            time_index = range(len(lows))
            
            # Simple rising support check
            first_quarter_low = lows.iloc[:len(lows)//4].min()
            last_quarter_low = lows.iloc[-len(lows)//4:].min()
            
            if resistance_touches >= 2 and last_quarter_low > first_quarter_low:
                # Breakout above resistance
                current_price = df_local.iloc[i]['close']
                current_volume = df_local.iloc[i]['volume']
                avg_volume = triangle_data['volume'].mean()
                
                if current_price > resistance_level and current_volume > (avg_volume * 1.3):
                    patterns.append(i)
        
        return patterns
    
    ascending_triangle_patterns = detect_ascending_triangle(df)
    df['pattern_ascending_triangle'] = False
    if ascending_triangle_patterns:
        for idx in ascending_triangle_patterns:
            if idx < len(df):
                df.iloc[idx, df.columns.get_loc('pattern_ascending_triangle')] = True
    
    print("✅ Hoàn thành phát hiện mẫu hình lớn!")
    return df

def get_market_context():
    """
    🌊 Lấy bối cảnh thị trường chung (VNINDEX) theo hệ thống GTI
    """
    print("\n🌊 Đang phân tích bối cảnh thị trường...")
    
    try:
        # Lấy dữ liệu VNINDEX
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        vnindex_df = lay_du_lieu_co_phieu_vnstock("VNINDEX", start_date, end_date)
        
        if vnindex_df is None or vnindex_df.empty:
            return {
                "status": "error",
                "message": "Không thể lấy dữ liệu VNINDEX"
            }
        
        # Tính toán GTI cho VNINDEX
        vnindex_gti = tinh_toan_chi_bao_ky_thuat(vnindex_df)
        latest_vnindex = vnindex_gti.iloc[-1]
        
        # Phân tích trend VNINDEX
        vnindex_trend = "UPTREND" if latest_vnindex['gti_trend_check'] else "SIDEWAY/DOWNTREND"
        vnindex_score = int(latest_vnindex['gti_score'])
        
        # Đánh giá hiệu quả GTI theo market phase
        if vnindex_trend == "UPTREND" and vnindex_score >= 3:
            effectiveness = "CAO (70-80%)"
            recommendation = "Thích hợp cho chiến lược tích cực"
            max_position = "8-10% NAV per stock"
        elif vnindex_score >= 2:
            effectiveness = "TRUNG BÌNH (50-60%)" 
            recommendation = "Giảm tỷ trọng, chọn lọc kỹ"
            max_position = "5-7% NAV per stock"
        else:
            effectiveness = "THẤP (<50%)"
            recommendation = "Tránh xa hoặc trade với điểm ≥5"
            max_position = "3-5% NAV per stock"
        
        market_context = {
            "status": "success",
            "vnindex": {
                "current_price": round(float(latest_vnindex['close']), 2),
                "gti_score": vnindex_score,
                "trend": vnindex_trend,
                "trend_check": bool(latest_vnindex['gti_trend_check']),
                "recent_breakout": bool(latest_vnindex['gti_recent_breakout']),
                "near_high": bool(latest_vnindex['gti_dist_to_high_percent'] <= 15),
                "dist_to_high": round(float(latest_vnindex['gti_dist_to_high_percent']), 2)
            },
            "gti_effectiveness": {
                "current_market": vnindex_trend,
                "effectiveness_rate": effectiveness,
                "recommendation": recommendation,
                "max_position_size": max_position
            },
            "analysis_note": f"VNINDEX đang ở giai đoạn {vnindex_trend} với GTI score {vnindex_score}/4. "
                           f"Độ chính xác hệ thống GTI ước tính: {effectiveness}."
        }
        
        print(f"✅ VNINDEX: {latest_vnindex['close']:.1f} | GTI: {vnindex_score}/4 | Trend: {vnindex_trend}")
        return market_context
        
    except Exception as e:
        print(f"❌ Lỗi phân tích market context: {e}")
        return {
            "status": "error",
            "message": f"Lỗi phân tích thị trường: {str(e)}"
        }

def get_sector_analysis(stock_symbol: str):
    """
    🏭 Phân tích chỉ số ngành (đơn giản hoá - sử dụng các mã đại diện)
    """
    print(f"\n🏭 Đang phân tích ngành cho {stock_symbol}...")
    
    # Mapping mã cổ phiếu với ngành và mã đại diện
    sector_mapping = {
        # Banking
        "ACB": {"sector": "Ngân hàng", "representative": "VCB"},
        "BID": {"sector": "Ngân hàng", "representative": "VCB"}, 
        "CTG": {"sector": "Ngân hàng", "representative": "VCB"},
        "HDB": {"sector": "Ngân hàng", "representative": "VCB"},
        "MBB": {"sector": "Ngân hàng", "representative": "VCB"},
        "STB": {"sector": "Ngân hàng", "representative": "VCB"},
        "TCB": {"sector": "Ngân hàng", "representative": "VCB"},
        "TPB": {"sector": "Ngân hàng", "representative": "VCB"},
        "VCB": {"sector": "Ngân hàng", "representative": "VCB"},
        "VPB": {"sector": "Ngân hàng", "representative": "VCB"},
        "VIB": {"sector": "Ngân hàng", "representative": "VCB"},
        
        # Real Estate
        "VHM": {"sector": "Bất động sản", "representative": "VIC"},
        "VIC": {"sector": "Bất động sản", "representative": "VIC"},
        "VRE": {"sector": "Bất động sản", "representative": "VIC"},
        
        # Technology
        "FPT": {"sector": "Công nghệ", "representative": "FPT"},
        
        # Steel
        "HPG": {"sector": "Thép", "representative": "HPG"},
        
        # Retail
        "MWG": {"sector": "Bán lẻ", "representative": "MWG"},
        
        # Oil & Gas
        "GAS": {"sector": "Dầu khí", "representative": "GAS"},
        "PLX": {"sector": "Dầu khí", "representative": "GAS"},
        
        # Food & Beverage
        "VNM": {"sector": "Thực phẩm", "representative": "VNM"},
        "MSN": {"sector": "Thực phẩm", "representative": "VNM"},
        "SAB": {"sector": "Thực phẩm", "representative": "VNM"},
    }
    
    sector_info = sector_mapping.get(stock_symbol.upper())
    
    if not sector_info:
        return {
            "status": "unknown_sector",
            "message": f"Chưa có thông tin ngành cho {stock_symbol}"
        }
    
    try:
        # Lấy dữ liệu mã đại diện ngành
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        sector_df = lay_du_lieu_co_phieu_vnstock(sector_info["representative"], start_date, end_date)
        
        if sector_df is None or sector_df.empty:
            return {
                "status": "error", 
                "message": f"Không thể lấy dữ liệu ngành {sector_info['sector']}"
            }
        
        # Tính GTI cho ngành
        sector_gti = tinh_toan_chi_bao_ky_thuat(sector_df)
        latest_sector = sector_gti.iloc[-1]
        sector_score = int(latest_sector['gti_score'])
        
        sector_trend = "TÍCH CỰC" if latest_sector['gti_trend_check'] else "TIÊU CỰC"
        
        sector_analysis = {
            "status": "success",
            "sector_name": sector_info["sector"],
            "representative_stock": sector_info["representative"],
            "sector_gti_score": sector_score,
            "sector_trend": sector_trend,
            "sector_price": round(float(latest_sector['close']), 2),
            "analysis_note": f"Ngành {sector_info['sector']} (đại diện: {sector_info['representative']}) "
                           f"có GTI score {sector_score}/4, xu hướng {sector_trend}."
        }
        
        print(f"✅ Ngành {sector_info['sector']}: GTI {sector_score}/4 | {sector_trend}")
        return sector_analysis
        
    except Exception as e:
        print(f"❌ Lỗi phân tích ngành: {e}")
        return {
            "status": "error",
            "message": f"Lỗi phân tích ngành: {str(e)}"
        }

def prepare_news_search_context(stock_symbol: str, sector_name: str = None):
    """
    📰 Chuẩn bị context cho ChatGPT search tin tức
    QUAN TRỌNG: Chỉ search tin tức, sự kiện - KHÔNG search dữ liệu giá, volume, chỉ số kỹ thuật
    """
    search_contexts = {
        "company_news": f"tin tức mới nhất về công ty {stock_symbol} Việt Nam",
        "earnings_news": f"kết quả kinh doanh {stock_symbol} 2024 2025",
        "industry_events": f"tin tức ngành {sector_name if sector_name else 'chứng khoán'} Việt Nam",
        "policy_updates": f"chính sách ảnh hưởng ngành {sector_name if sector_name else 'tài chính'} Việt Nam"
    }
    
    return {
        "search_instruction": f"""
🔍 HƯỚNG DẪN SEARCH TIN TỨC CHO {stock_symbol}:

✅ CẦN TÌM:
- Tin tức công ty: {search_contexts['company_news']}
- Kết quả kinh doanh: {search_contexts['earnings_news']}
- Sự kiện ngành: {search_contexts['industry_events']}
- Chính sách liên quan: {search_contexts['policy_updates']}

❌ TUYỆT ĐỐI KHÔNG TÌM:
- Dữ liệu giá cổ phiếu, volume, chỉ số kỹ thuật
- Dự đoán giá, forecast
- Phân tích kỹ thuật từ bên ngoài

📊 LƯU Ý: Tất cả dữ liệu về giá và chỉ số kỹ thuật đã được cung cấp qua API.
        """,
        "suggested_searches": list(search_contexts.values())
    }

def comprehensive_gti_analysis(stock_symbol: str, start_date: str = None, end_date: str = None):
    """
    🚀 Phân tích GTI Pro v2.0 TOÀN DIỆN:
    1. GTI Core (4 tiêu chí) + Enhanced Patterns (16 patterns)
    2. Market Context (VNINDEX) + Sector Analysis
    3. News Search Context cho ChatGPT
    4. Combined Scoring & Recommendations
    """
    print(f"\n🚀 BẮT ĐẦU PHÂN TÍCH GTI PRO v2.0 TOÀN DIỆN CHO {stock_symbol}")
    print("="*80)
    
    # Tính toán thời gian mặc định
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    try:
        # BƯỚC 1: Lấy dữ liệu cơ bản
        print("📊 BƯỚC 1: Lấy dữ liệu cơ bản...")
        df = lay_du_lieu_co_phieu_vnstock(stock_symbol, start_date, end_date)
        
        if df is None or df.empty:
            return {
                "status": "error",
                "message": f"Không thể lấy dữ liệu cho {stock_symbol}"
            }
        
        # BƯỚC 2: GTI Core Analysis
        print("🔥 BƯỚC 2: Phân tích GTI Core...")
        df_gti = tinh_toan_chi_bao_ky_thuat(df)
        
        # BƯỚC 3: Basic Pattern Detection
        print("🎯 BƯỚC 3: Phát hiện Basic Patterns...")
        df_patterns = detect_free_patterns(df_gti)
        
        # BƯỚC 4: Large Chart Patterns  
        print("📈 BƯỚC 4: Phát hiện Large Chart Patterns...")
        df_patterns = detect_large_chart_patterns(df_patterns)
        
        # BƯỚC 5: Pattern Analysis
        print("📊 BƯỚC 5: Phân tích Pattern Results...")
        pattern_results = phan_tich_pattern_results(df_patterns, stock_symbol)
        
        # BƯỚC 6: Market Context Analysis
        print("🌊 BƯỚC 6: Phân tích Market Context...")
        market_context = get_market_context()
        
        # BƯỚC 7: Sector Analysis
        print("🏭 BƯỚC 7: Phân tích Sector...")
        sector_analysis = get_sector_analysis(stock_symbol)
        
        # BƯỚC 8: News Search Context
        print("📰 BƯỚC 8: Chuẩn bị News Search Context...")
        sector_name = sector_analysis.get('sector_name') if sector_analysis.get('status') == 'success' else None
        news_context = prepare_news_search_context(stock_symbol, sector_name)
        
        # BƯỚC 9: Combined Scoring v2.0
        print("⚡ BƯỚC 9: Tính toán Enhanced Scoring...")
        latest = df_patterns.iloc[-1]
        
        # GTI Score (0-4) - ép kiểu về int Python
        gti_score = int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0
        
        # Basic Pattern Scores - đảm bảo kiểu int Python
        basic_bullish = int(pattern_results.get('bullish_score', 0))
        basic_bearish = int(pattern_results.get('bearish_score', 0))
        
        # Large Pattern Scores (×2 points)
        large_patterns = ['cup_handle', 'bull_flag', 'base_n_break', 'ascending_triangle']
        large_bullish_score = 0
        for pattern in large_patterns:
            if f'pattern_{pattern}' in df_patterns.columns and latest[f'pattern_{pattern}']:
                large_bullish_score += 2  # Large patterns worth 2 points each
        
        # Base Score: GTI + Basic + Large
        base_score = gti_score + basic_bullish - basic_bearish + large_bullish_score
        
        # Market Context Adjustments
        market_adjustment = 0
        if market_context.get('status') == 'success':
            vnindex_gti = market_context['vnindex']['gti_score']
            if vnindex_gti >= 3:  # VNINDEX uptrend
                market_adjustment += 0.5
            elif vnindex_gti <= 1:  # VNINDEX downtrend
                market_adjustment -= 0.5
        
        # Sector Adjustment
        sector_adjustment = 0
        if sector_analysis.get('status') == 'success':
            if sector_analysis['sector_trend'] == 'TÍCH CỰC':
                sector_adjustment += 0.25
            elif sector_analysis['sector_trend'] == 'TIÊU CỰC':
                sector_adjustment -= 0.25
        
        # Final Combined Score
        combined_score = base_score + market_adjustment + sector_adjustment
        
        # Enhanced Recommendations
        if combined_score >= 6:
            recommendation = {
                "level": "CỰC KỲ TÍCH CỰC", 
                "action": "STRONG BUY",
                "emoji": "🟢",
                "position_size": "8-12% NAV",
                "message": "Cơ hội đầu tư xuất sắc với điểm số cao"
            }
        elif combined_score >= 4:
            recommendation = {
                "level": "RẤT TÍCH CỰC", 
                "action": "CÂN NHẮC MUA",
                "emoji": "🟢", 
                "position_size": "5-8% NAV",
                "message": "Cơ hội tốt, cân nhắc mua vào"
            }
        elif combined_score >= 2:
            recommendation = {
                "level": "TÍCH CỰC", 
                "action": "THEO DÕI",
                "emoji": "🟡",
                "position_size": "3-5% NAV", 
                "message": "Theo dõi và chờ tín hiệu rõ hơn"
            }
        elif combined_score >= 0:
            recommendation = {
                "level": "TRUNG TÍNH", 
                "action": "CHỜ TÍN HIỆU",
                "emoji": "🟠",
                "position_size": "0-3% NAV",
                "message": "Chưa có tín hiệu rõ ràng, chờ đợi"
            }
        else:
            recommendation = {
                "level": "TIÊU CỰC", 
                "action": "TRÁNH XA",
                "emoji": "🔴",
                "position_size": "0% NAV", 
                "message": "Tránh xa hoặc chờ cải thiện"
            }
        
        # BƯỚC 10: Tạo kết quả comprehensive
        result = {
            "status": "success",
            "analysis_date": latest.name.strftime("%Y-%m-%d") if hasattr(latest.name, 'strftime') else str(latest.name),
            "stock_symbol": stock_symbol.upper(),
            "closing_price": round(float(latest['close']), 2),
            
            # GTI Analysis
            "gti_analysis": {
                "gti_score": int(gti_score),
                "gti_criteria": {
                    "trend_check": bool(latest['gti_trend_check']) if pd.notna(latest['gti_trend_check']) else False,
                    "recent_breakout": bool(latest['gti_recent_breakout']) if pd.notna(latest['gti_recent_breakout']) else False,
                    "near_one_year_high": bool(latest['gti_dist_to_high_percent'] <= 15) if pd.notna(latest['gti_dist_to_high_percent']) else False,
                    "is_pullback": bool(latest['gti_is_pullback']) if pd.notna(latest['gti_is_pullback']) else False
                }
            },
            
            # Enhanced Pattern Analysis
            "pattern_analysis": {
                "basic_bullish_score": int(basic_bullish),
                "basic_bearish_score": int(basic_bearish),
                "large_patterns_score": int(large_bullish_score),
                "current_patterns": pattern_results.get('current_patterns', []),
                "pattern_summary": f"{basic_bullish}B/{basic_bearish}Be + {large_bullish_score//2}L"
            },
            
            # Market Context & Sector
            "market_context": market_context,
            "sector_analysis": sector_analysis,
            
            # Combined Analysis
            "combined_analysis": {
                "base_score": int(base_score),
                "market_adjustment": market_adjustment,
                "sector_adjustment": sector_adjustment,
                "total_score": round(combined_score, 2),
                "final_recommendation": recommendation
            },
            
            # News Search Context for ChatGPT
            "news_search_context": news_context,
            
            # Technical Levels
            "technical_levels": {
                "support_level": round(float(latest['support_level']), 2) if pd.notna(latest['support_level']) else None,
                "resistance_level": round(float(latest['resistance_level']), 2) if pd.notna(latest['resistance_level']) else None,
                "EMA10": round(float(latest['EMA10']), 2) if pd.notna(latest['EMA10']) else None,
                "EMA20": round(float(latest['EMA20']), 2) if pd.notna(latest['EMA20']) else None
            },
            
            # System Info
            "system_info": {
                "version": "GTI Pro v2.0",
                "scoring_range": "-5 to +18 points",
                "enhanced_features": ["Large Patterns", "Market Context", "Sector Analysis", "News Integration"]
            }
        }
        
        print("✅ HOÀN THÀNH PHÂN TÍCH GTI PRO v2.0!")
        print(f"📊 KẾT QUẢ: {combined_score:.1f} điểm - {recommendation['emoji']} {recommendation['level']}")
        
        return result
        
    except Exception as e:
        print(f"❌ LỖI PHÂN TÍCH: {e}")
        return {
            "status": "error",
            "message": f"Lỗi phân tích {stock_symbol}: {str(e)}"
        }

def scan_single_stock(stock_symbol: str, min_gti_score: int = 2, min_combined_score: int = 3):
    """
    🔍 Quét một mã cổ phiếu đơn lẻ và trả về kết quả nếu đạt tiêu chí
    """
    try:
        # Tính toán thời gian
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Lấy dữ liệu
        df = lay_du_lieu_co_phieu_vnstock(stock_symbol, start_date, end_date)
        
        if df is None or df.empty:
            return None
        
        # Tính toán GTI
        df_analyzed = tinh_toan_chi_bao_ky_thuat(df)
        
        # Phát hiện patterns
        df_patterns = detect_free_patterns(df_analyzed)
        df_patterns = detect_large_chart_patterns(df_patterns)
        
        # Phân tích kết quả patterns
        pattern_results = phan_tich_pattern_results(df_patterns, stock_symbol)
        
        # Lấy dữ liệu gần nhất
        latest = df_patterns.iloc[-1]
        
        # Tính điểm
        gti_score = int(latest['gti_score']) if pd.notna(latest['gti_score']) else 0
        bullish_score = int(pattern_results.get('bullish_score', 0))
        bearish_score = int(pattern_results.get('bearish_score', 0))
        combined_score = gti_score + bullish_score - bearish_score
        
        # Lọc theo tiêu chí
        if gti_score >= min_gti_score and combined_score >= min_combined_score:
            # Lấy đánh giá
            evaluation = GTIConfig.get_score_evaluation(combined_score)
            
            return {
                "stock_symbol": stock_symbol,
                "current_price": round(float(latest['close']), 2),
                "volume": int(latest['volume']) if pd.notna(latest['volume']) else 0,
                "gti_score": gti_score,
                "pattern_score": {
                    "bullish": bullish_score,
                    "bearish": bearish_score,
                    "net": bullish_score - bearish_score
                },
                "combined_score": combined_score,
                "evaluation": evaluation,
                "key_metrics": {
                    "gti_trend_check": bool(latest['gti_trend_check']) if pd.notna(latest['gti_trend_check']) else False,
                    "gti_recent_breakout": bool(latest['gti_recent_breakout']) if pd.notna(latest['gti_recent_breakout']) else False,
                    "gti_dist_to_high_percent": round(float(latest['gti_dist_to_high_percent']), 2) if pd.notna(latest['gti_dist_to_high_percent']) else None,
                    "gti_is_pullback": bool(latest['gti_is_pullback']) if pd.notna(latest['gti_is_pullback']) else False
                },
                "technical_levels": {
                    "support": round(float(latest['support_level']), 2) if pd.notna(latest['support_level']) else None,
                    "resistance": round(float(latest['resistance_level']), 2) if pd.notna(latest['resistance_level']) else None,
                    "ema10": round(float(latest['EMA10']), 2) if pd.notna(latest['EMA10']) else None,
                    "ema20": round(float(latest['EMA20']), 2) if pd.notna(latest['EMA20']) else None
                },
                "current_patterns": pattern_results.get('current_patterns', []),
                "scan_timestamp": datetime.now().isoformat()
            }
        
        return None  # Không đạt tiêu chí
        
    except Exception as e:
        print(f"❌ Lỗi khi quét {stock_symbol}: {str(e)}")
        return None

def market_scan_parallel(stock_list: list, 
                        min_gti_score: int = 2, 
                        min_combined_score: int = 3,
                        max_workers: int = None,
                        timeout: int = None):
    """
    🚀 Quét thị trường song song với ThreadPoolExecutor - OPTIMIZED v2.0
    
    Args:
        stock_list: Danh sách mã cổ phiếu
        min_gti_score: Điểm GTI tối thiểu
        min_combined_score: Điểm tổng hợp tối thiểu
        max_workers: Số thread tối đa (auto-detect nếu None)
        timeout: Timeout tổng cộng (giây, auto-calculate nếu None)
    
    Returns:
        Dict chứa kết quả scan và thống kê
    """
    
    # Auto-configure performance parameters
    if max_workers is None:
        max_workers = GTIConfig.MARKET_SCAN_BATCH_SIZE
    
    if timeout is None:
        # Progressive timeout: 10s base + 5s per stock, min 60s, max 600s
        if GTIConfig.ENABLE_PROGRESSIVE_TIMEOUT:
            timeout = min(max(60, 10 + len(stock_list) * 5), GTIConfig.MARKET_SCAN_TIMEOUT)
        else:
            timeout = GTIConfig.MARKET_SCAN_TIMEOUT
    
    print(f"🔍 Bắt đầu quét {len(stock_list)} mã cổ phiếu song song...")
    print(f"⚙️  Tiêu chí: GTI >= {min_gti_score}, Combined >= {min_combined_score}")
    print(f"🔧 Cấu hình: {max_workers} workers, timeout {timeout}s")
    
    start_time = time.time()
    results = []
    errors = []
    processed_count = 0
    
    # Chunked processing for large lists
    if len(stock_list) > GTIConfig.CHUNK_SIZE_FOR_LARGE_SCANS:
        print(f"📦 Chia nhỏ {len(stock_list)} mã thành chunks của {GTIConfig.CHUNK_SIZE_FOR_LARGE_SCANS}")
        
        chunk_size = GTIConfig.CHUNK_SIZE_FOR_LARGE_SCANS
        for i in range(0, len(stock_list), chunk_size):
            chunk = stock_list[i:i + chunk_size]
            chunk_timeout = min(timeout // 3, 300)  # Chia timeout cho từng chunk
            
            print(f"🔄 Xử lý chunk {i//chunk_size + 1}: {len(chunk)} mã (timeout: {chunk_timeout}s)")
            
            chunk_results = _process_stock_chunk(
                chunk, min_gti_score, min_combined_score, 
                max_workers, chunk_timeout
            )
            
            results.extend(chunk_results['results'])
            errors.extend(chunk_results['errors'])
            processed_count += chunk_results['processed']
            
            # Check if we're running out of time
            elapsed = time.time() - start_time
            if elapsed > timeout * 0.8:  # 80% of total timeout
                print(f"⚠️ Đã sử dụng 80% thời gian, dừng scan để tránh timeout")
                break
    else:
        # Normal processing for smaller lists
        chunk_results = _process_stock_chunk(
            stock_list, min_gti_score, min_combined_score,
            max_workers, timeout
        )
        results = chunk_results['results']
        errors = chunk_results['errors']
        processed_count = chunk_results['processed']
    
    # Sắp xếp kết quả theo điểm giảm dần
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # Thống kê
    execution_time = time.time() - start_time
    success_count = len(results)
    error_count = len(errors)
    total_stocks = len(stock_list)
    
    print(f"\n📊 KẾT QUẢ QUÉT THỊ TRƯỜNG:")
    print(f"   ⏱️  Thời gian: {execution_time:.1f}s")
    print(f"   ✅ Xử lý: {processed_count}/{total_stocks}")
    print(f"   🎯 Đạt tiêu chí: {success_count} mã")
    print(f"   ❌ Lỗi: {error_count}")
    
    return {
        "scan_results": results,
        "statistics": {
            "total_scanned": total_stocks,
            "processed_count": processed_count,
            "success_count": success_count,
            "qualified_count": len(results),
            "error_count": error_count,
            "execution_time_seconds": round(execution_time, 2),
            "scan_criteria": {
                "min_gti_score": min_gti_score,
                "min_combined_score": min_combined_score
            },
            "performance_config": {
                "max_workers": max_workers,
                "timeout_used": timeout,
                "chunked_processing": len(stock_list) > GTIConfig.CHUNK_SIZE_FOR_LARGE_SCANS
            }
        },
        "errors": errors,
        "scan_timestamp": datetime.now().isoformat()
    }

def _process_stock_chunk(stock_list: list, min_gti_score: int, min_combined_score: int,
                        max_workers: int, timeout: int):
    """
    🔧 Xử lý một chunk stocks với timeout handling tốt hơn
    """
    results = []
    errors = []
    processed = 0
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Tạo futures cho tất cả mã trong chunk
            future_to_stock = {
                executor.submit(scan_single_stock, stock, min_gti_score, min_combined_score): stock 
                for stock in stock_list
            }
            
            # Xử lý kết quả với timeout per stock
            for future in concurrent.futures.as_completed(future_to_stock, timeout=timeout):
                stock = future_to_stock[future]
                processed += 1
                
                try:
                    result = future.result(timeout=GTIConfig.SINGLE_STOCK_TIMEOUT)
                    if result is not None:
                        results.append(result)
                        print(f"✅ {stock}: Tổng điểm {result['combined_score']}")
                    else:
                        print(f"⏭️  {stock}: Không đạt tiêu chí")
                except Exception as e:
                    error_msg = f"{stock}: {str(e)}"
                    errors.append(error_msg)
                    print(f"❌ {error_msg}")
    
    except concurrent.futures.TimeoutError:
        print(f"⏰ Chunk timeout sau {timeout} giây! Đã xử lý {processed}/{len(stock_list)}")
    
    return {
        "results": results,
        "errors": errors,
        "processed": processed
    }

def market_scan_by_category(category: str = "vn30", 
                           min_gti_score: int = 2, 
                           min_combined_score: int = 3):
    """
    🎯 Quét thị trường theo danh mục cụ thể
    
    Args:
        category: Loại danh sách (vn30, top100, popular, hoặc tên ngành)
        min_gti_score: Điểm GTI tối thiểu
        min_combined_score: Điểm tổng hợp tối thiểu
    
    Returns:
        Kết quả scan với thông tin danh mục
    """
    print(f"🔍 Quét thị trường theo danh mục: {category.upper()}")
    
    # Lấy danh sách mã theo danh mục
    stock_list = GTIConfig.get_stock_list_by_type(category)
    
    if not stock_list:
        return {
            "error": f"Không tìm thấy danh mục {category}",
            "available_categories": ["vn30", "top100", "popular"] + list(GTIConfig.SECTOR_STOCKS.keys())
        }
    
    print(f"📋 Danh sách: {len(stock_list)} mã cổ phiếu")
    
    # Thực hiện scan
    scan_result = market_scan_parallel(
        stock_list=stock_list,
        min_gti_score=min_gti_score,
        min_combined_score=min_combined_score,
        max_workers=GTIConfig.MARKET_SCAN_BATCH_SIZE,
        timeout=GTIConfig.MARKET_SCAN_TIMEOUT
    )
    
    # Thêm thông tin danh mục
    scan_result["category_info"] = {
        "category_name": category,
        "category_stocks": stock_list,
        "category_size": len(stock_list)
    }
    
    return scan_result

def market_scan_top_picks(limit: int = 20, quick_mode: bool = None):
    """
    🏆 Quét và trả về TOP mã cổ phiếu tốt nhất toàn thị trường - SECTOR-BASED v3.0
    
    Args:
        limit: Số lượng mã top cần trả về
        quick_mode: Chế độ nhanh (auto-detect từ config nếu None)
    
    Returns:
        Top picks với phân tích chi tiết
    """
    if quick_mode is None:
        quick_mode = GTIConfig.TOP_PICKS_QUICK_MODE
    
    print(f"🏆 Tìm kiếm TOP {limit} mã cổ phiếu tốt nhất bằng SECTOR-BASED approach...")
    if quick_mode:
        print("⚡ Sử dụng QUICK MODE - quét ít mã từ mỗi sector")
    
    # Quick mode: Scan 10 mã đầu từ mỗi sector (tổng ~100 mã)
    if quick_mode:
        # Stage 1: Scan VN30 + Popular trước
        priority_stocks = list(set(GTIConfig.VN30_STOCKS + GTIConfig.POPULAR_STOCKS))
        print(f"🎯 Stage 1: Quét {len(priority_stocks)} mã ưu tiên...")
        
        stage1_result = market_scan_parallel(
            stock_list=priority_stocks,
            min_gti_score=1,
            min_combined_score=1,
            max_workers=GTIConfig.MARKET_SCAN_BATCH_SIZE,
            timeout=120  # 2 phút cho stage 1
        )
        
        # Nếu đã có đủ kết quả chất lượng cao, return luôn
        high_quality_results = [
            stock for stock in stage1_result["scan_results"] 
            if stock["combined_score"] >= 4
        ]
        
        if len(high_quality_results) >= limit:
            print(f"✅ Đã tìm thấy {len(high_quality_results)} mã chất lượng cao từ stage 1")
            top_picks = high_quality_results[:limit]
            combined_stats = stage1_result["statistics"]
            combined_stats["quick_mode_used"] = True
            combined_stats["scan_method"] = "priority_only"
        else:
            # Stage 2: Scan top 10 từ mỗi sector
            sector_stocks = GTIConfig.get_all_sectors_combined(limit_per_sector=10)
            remaining_stocks = [
                stock for stock in sector_stocks 
                if stock not in priority_stocks
            ]
            
            needed = limit - len(high_quality_results)
            print(f"🔄 Stage 2: Cần thêm {needed} mã, quét top 10 từ {len(GTIConfig.SECTOR_STOCKS)} sectors...")
            
            stage2_result = market_scan_parallel(
                stock_list=remaining_stocks,
                min_gti_score=1,
                min_combined_score=1,
                max_workers=GTIConfig.MARKET_SCAN_BATCH_SIZE,
                timeout=240  # 4 phút cho stage 2
            )
            
            # Combine results
            all_results = stage1_result["scan_results"] + stage2_result["scan_results"]
            all_results.sort(key=lambda x: x['combined_score'], reverse=True)
            top_picks = all_results[:limit]
            
            # Combine statistics
            combined_stats = {
                "total_scanned": stage1_result["statistics"]["total_scanned"] + stage2_result["statistics"]["total_scanned"],
                "processed_count": stage1_result["statistics"]["processed_count"] + stage2_result["statistics"]["processed_count"],
                "success_count": len(all_results),
                "qualified_count": len(all_results),
                "error_count": stage1_result["statistics"]["error_count"] + stage2_result["statistics"]["error_count"],
                "execution_time_seconds": stage1_result["statistics"]["execution_time_seconds"] + stage2_result["statistics"]["execution_time_seconds"],
                "quick_mode_used": True,
                "scan_method": "sector_based_limited",
                "stages": {
                    "stage1": stage1_result["statistics"],
                    "stage2": stage2_result["statistics"]
                }
            }
    else:
        # Normal mode: Scan nhiều hơn từ các sectors
        print("🔍 Sử dụng NORMAL MODE - quét nhiều hơn từ các sectors")
        sector_stocks = GTIConfig.get_all_sectors_combined(limit_per_sector=20)  # Top 20 từ mỗi sector
        
        print(f"📊 Sẽ quét {len(sector_stocks)} mã từ {len(GTIConfig.SECTOR_STOCKS)} sectors")
        
        scan_result = market_scan_parallel(
            stock_list=sector_stocks,
            min_gti_score=1,
            min_combined_score=1,
            max_workers=GTIConfig.MARKET_SCAN_BATCH_SIZE,
            timeout=GTIConfig.MARKET_SCAN_TIMEOUT
        )
        
        if not scan_result["scan_results"]:
            return {
                "message": "Không tìm thấy mã nào đạt tiêu chí cơ bản",
                "scan_info": scan_result["statistics"]
            }
        
        top_picks = scan_result["scan_results"][:limit]
        combined_stats = scan_result["statistics"]
        combined_stats["quick_mode_used"] = False
        combined_stats["scan_method"] = "sector_based_full"
    
    # Phân loại theo mức độ
    categorized_picks = {
        "very_strong": [stock for stock in top_picks if stock["combined_score"] >= 6],
        "strong": [stock for stock in top_picks if 4 <= stock["combined_score"] < 6],
        "moderate": [stock for stock in top_picks if 2 <= stock["combined_score"] < 4],
        "weak_but_potential": [stock for stock in top_picks if stock["combined_score"] < 2]
    }
    
    # Thống kê theo ngành
    sector_distribution = {}
    for stock in top_picks:
        symbol = stock["stock_symbol"]
        for sector, stocks in GTIConfig.SECTOR_STOCKS.items():
            if symbol in stocks:
                if sector not in sector_distribution:
                    sector_distribution[sector] = []
                sector_distribution[sector].append(symbol)
                break
    
    return {
        "top_picks": top_picks,
        "categorized_picks": categorized_picks,
        "sector_distribution": sector_distribution,
        "summary": {
            "total_found": len(top_picks) if quick_mode else len(scan_result["scan_results"]),
            "top_returned": len(top_picks),
            "very_strong_count": len(categorized_picks["very_strong"]),
            "strong_count": len(categorized_picks["strong"]),
            "moderate_count": len(categorized_picks["moderate"])
        },
        "scan_info": combined_stats,
        "recommendation": get_market_scan_recommendation(top_picks),
        "scan_timestamp": datetime.now().isoformat()
    }

def get_market_scan_recommendation(top_picks: list) -> dict:
    """
    📋 Đưa ra khuyến nghị dựa trên kết quả market scan
    """
    if not top_picks:
        return {
            "status": "bearish",
            "message": "Thị trường không có cơ hội tốt, nên thận trọng",
            "action": "WAIT"
        }
    
    very_strong = len([s for s in top_picks if s["combined_score"] >= 6])
    strong = len([s for s in top_picks if 4 <= s["combined_score"] < 6])
    
    if very_strong >= 3:
        return {
            "status": "very_bullish",
            "message": f"Thị trường rất tích cực với {very_strong} mã rất mạnh",
            "action": "AGGRESSIVE_BUY",
            "max_position_per_stock": "8-10%",
            "total_portfolio_allocation": "80-90%"
        }
    elif strong >= 5:
        return {
            "status": "bullish", 
            "message": f"Thị trường tích cực với {strong} mã mạnh",
            "action": "SELECTIVE_BUY",
            "max_position_per_stock": "5-7%",
            "total_portfolio_allocation": "60-70%"
        }
    elif len(top_picks) >= 10:
        return {
            "status": "neutral_positive",
            "message": "Thị trường có cơ hội nhưng cần chọn lọc",
            "action": "CAREFUL_BUY",
            "max_position_per_stock": "3-5%", 
            "total_portfolio_allocation": "40-50%"
        }
    else:
        return {
            "status": "neutral",
            "message": "Thị trường ít cơ hội, nên đợi thời điểm tốt hơn",
            "action": "WAIT",
            "max_position_per_stock": "2-3%",
            "total_portfolio_allocation": "20-30%"
        }

# Đoạn mã để chạy thử
if __name__ == "__main__":
    ma_can_kiem_tra = "FPT"
    
    print("🚀 CHẠY THỬ COMPREHENSIVE GTI ANALYSIS v2.0")
    print("="*50)
    
    # Test comprehensive analysis
    ket_qua_comprehensive = comprehensive_gti_analysis(ma_can_kiem_tra)
    
    if ket_qua_comprehensive['status'] == 'success':
        print(f"\n📊 KẾT QUẢ COMPREHENSIVE CHO {ma_can_kiem_tra}:")
        print(f"GTI Score: {ket_qua_comprehensive['gti_analysis']['gti_score']}/4")
        print(f"Pattern Score: {ket_qua_comprehensive['pattern_analysis']['pattern_summary']}")
        print(f"Combined Score: {ket_qua_comprehensive['combined_analysis']['total_score']}")
        print(f"Recommendation: {ket_qua_comprehensive['combined_analysis']['final_recommendation']['emoji']} {ket_qua_comprehensive['combined_analysis']['final_recommendation']['level']}")
        
        print(f"\n📰 NEWS SEARCH CONTEXT:")
        print(ket_qua_comprehensive['news_search_context']['search_instruction'])
    else:
        print(f"❌ Lỗi: {ket_qua_comprehensive['message']}")
        
        # Fallback to old method
        print("\n🔄 Chạy phân tích cũ...")
        du_lieu = lay_du_lieu_co_phieu_vnstock(
            ma_co_phieu=ma_can_kiem_tra,
            start_date="2024-01-01",
            end_date="2025-06-28"
        )

        if du_lieu is not None:
            print(f"Đã lấy được {len(du_lieu)} bản ghi cho mã {ma_can_kiem_tra}.")
            
            du_lieu_phan_tich = tinh_toan_chi_bao_ky_thuat(du_lieu)
            latest = du_lieu_phan_tich.iloc[-1]
            print(f"\nKết quả cơ bản:")
            print(f"Giá đóng cửa: {latest['close']:,.0f} VND")
            print(f"GTI Score: {latest['gti_score']}/4")
            print(f"GTI Signal: {latest['gti_signal']}")
        else:
            print("Không thể lấy dữ liệu. Vui lòng:")
            print("1. Kiểm tra kết nối internet")
            print("2. Cài đặt vnstock: pip install vnstock")
            print("3. Cài đặt ta: pip install ta")
            print("4. Thử lại với mã cổ phiếu khác")