#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 GTI Cache Manager - In-Memory Caching System
Optimize performance cho stock analysis và market scanning
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from config import GTIConfig
import json
import hashlib

class GTICacheManager:
    """
    🚀 In-Memory Cache Manager cho GTI Stock Analysis
    """
    
    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.enabled = GTIConfig.ENABLE_CACHE
        self.default_expiry = GTIConfig.CACHE_EXPIRY_MINUTES * 60  # Convert to seconds
        self.single_stock_cache = GTIConfig.CACHE_SINGLE_STOCK_RESULTS
        
        print(f"🚀 GTI Cache Manager initialized")
        print(f"   Cache enabled: {self.enabled}")
        print(f"   Default expiry: {GTIConfig.CACHE_EXPIRY_MINUTES} minutes")
        print(f"   Single stock cache: {self.single_stock_cache}")
    
    def _generate_cache_key(self, operation: str, **kwargs) -> str:
        """
        🔑 Tạo cache key duy nhất từ operation và parameters
        """
        # Sắp xếp kwargs để đảm bảo key consistent
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        
        # Hash để tạo key ngắn gọn
        hash_obj = hashlib.md5(f"{operation}:{params_str}".encode())
        return f"gti_{operation}_{hash_obj.hexdigest()[:8]}"
    
    def get(self, operation: str, **kwargs) -> Optional[Any]:
        """
        🔍 Lấy dữ liệu từ cache nếu có và chưa hết hạn
        """
        if not self.enabled:
            return None
        
        cache_key = self._generate_cache_key(operation, **kwargs)
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # Kiểm tra expiry
            if time.time() < cache_entry['expires_at']:
                cache_entry['hits'] += 1
                cache_entry['last_accessed'] = time.time()
                
                print(f"✅ Cache HIT for {operation} (hits: {cache_entry['hits']})")
                return cache_entry['data']
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
                print(f"⏰ Cache EXPIRED for {operation}")
        
        return None
    
    def set(self, operation: str, data: Any, expiry_seconds: int = None, **kwargs):
        """
        💾 Lưu dữ liệu vào cache
        """
        if not self.enabled:
            return
        
        if expiry_seconds is None:
            expiry_seconds = self.default_expiry
        
        cache_key = self._generate_cache_key(operation, **kwargs)
        
        self.cache[cache_key] = {
            'data': data,
            'created_at': time.time(),
            'expires_at': time.time() + expiry_seconds,
            'last_accessed': time.time(),
            'hits': 0,
            'operation': operation,
            'params': kwargs
        }
        
        print(f"💾 Cache SET for {operation} (expire in {expiry_seconds}s)")
        
        # Cleanup old entries nếu cache quá lớn
        self._cleanup_if_needed()
    
    def _cleanup_if_needed(self):
        """
        🧹 Dọn dẹp cache nếu quá lớn (> 1000 entries)
        """
        if len(self.cache) > 1000:
            print("🧹 Cache cleanup: removing expired and least used entries...")
            
            current_time = time.time()
            
            # Remove expired entries first
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            # If still too many, remove least used
            if len(self.cache) > 800:
                sorted_by_hits = sorted(
                    self.cache.items(),
                    key=lambda x: (x[1]['hits'], x[1]['last_accessed'])
                )
                
                # Remove bottom 200 entries
                for key, _ in sorted_by_hits[:200]:
                    del self.cache[key]
            
            print(f"   Cache size after cleanup: {len(self.cache)}")
    
    def invalidate(self, operation: str = None, **kwargs):
        """
        🗑️ Xóa cache entries
        """
        if not self.enabled:
            return
        
        if operation is None:
            # Clear all cache
            self.cache.clear()
            print("🗑️ All cache cleared")
        else:
            cache_key = self._generate_cache_key(operation, **kwargs)
            if cache_key in self.cache:
                del self.cache[cache_key]
                print(f"🗑️ Cache invalidated for {operation}")
    
    def get_stats(self) -> Dict:
        """
        📊 Thống kê cache performance
        """
        if not self.enabled:
            return {"cache_enabled": False}
        
        current_time = time.time()
        total_entries = len(self.cache)
        expired_entries = sum(
            1 for entry in self.cache.values()
            if current_time > entry['expires_at']
        )
        
        total_hits = sum(entry['hits'] for entry in self.cache.values())
        
        operations = {}
        for entry in self.cache.values():
            op = entry['operation']
            if op not in operations:
                operations[op] = {'count': 0, 'hits': 0}
            operations[op]['count'] += 1
            operations[op]['hits'] += entry['hits']
        
        return {
            "cache_enabled": True,
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "valid_entries": total_entries - expired_entries,
            "total_hits": total_hits,
            "operations": operations,
            "memory_usage_estimate": f"{total_entries * 0.5:.1f} KB"
        }

# Global cache instance
gti_cache = GTICacheManager()

def cache_stock_analysis(stock_symbol: str, min_gti_score: int = 2, min_combined_score: int = 3):
    """
    🔍 Cache wrapper cho single stock analysis
    """
    cache_key_params = {
        'stock_symbol': stock_symbol.upper(),
        'min_gti_score': min_gti_score,
        'min_combined_score': min_combined_score
    }
    
    # Try to get from cache first
    cached_result = gti_cache.get('single_stock', **cache_key_params)
    if cached_result:
        return cached_result
    
    # If not in cache, compute and store
    from lay_data_stock import scan_single_stock
    
    result = scan_single_stock(stock_symbol, min_gti_score, min_combined_score)
    
    if result and gti_cache.single_stock_cache:
        # Cache for shorter time for individual stocks (2 minutes)
        gti_cache.set('single_stock', result, expiry_seconds=120, **cache_key_params)
    
    return result

def cache_market_scan(category: str, min_gti_score: int = 2, min_combined_score: int = 3):
    """
    🔍 Cache wrapper cho market scan by category
    """
    cache_key_params = {
        'category': category.lower(),
        'min_gti_score': min_gti_score,
        'min_combined_score': min_combined_score
    }
    
    # Try to get from cache first
    cached_result = gti_cache.get('market_scan', **cache_key_params)
    if cached_result:
        return cached_result
    
    # If not in cache, compute and store
    from lay_data_stock import market_scan_by_category
    
    result = market_scan_by_category(category, min_gti_score, min_combined_score)
    
    if result and 'scan_results' in result:
        # Cache market scans for longer (5 minutes default)
        gti_cache.set('market_scan', result, **cache_key_params)
    
    return result

# Test function
if __name__ == "__main__":
    print("🧪 Testing GTI Cache Manager...")
    
    # Test basic cache operations
    gti_cache.set('test_operation', {'result': 'test_data'}, test_param='value1')
    
    result1 = gti_cache.get('test_operation', test_param='value1')
    print(f"First get: {result1}")
    
    result2 = gti_cache.get('test_operation', test_param='value1')
    print(f"Second get (should be cache hit): {result2}")
    
    # Test cache stats
    stats = gti_cache.get_stats()
    print(f"Cache stats: {stats}")
    
    print("✅ Cache manager test completed!") 