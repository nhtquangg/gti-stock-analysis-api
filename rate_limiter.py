#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ GTI Rate Limiter - Protect against VCI API rate limiting

Implement rate limiting protection:
- Delay between requests
- Retry logic with exponential backoff
- Request queue management
- Adaptive rate limiting
"""

import time
import threading
import random
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
import functools

class GTIRateLimiter:
    """
    🛡️ Rate Limiter cho VCI API calls
    """
    
    def __init__(self):
        self.last_request_time = 0
        self.min_delay = 0.5  # Minimum 0.5 seconds between requests
        self.base_delay = 1.0  # Base delay in seconds
        self.max_delay = 10.0  # Maximum delay
        self.current_delay = self.base_delay
        self.lock = threading.Lock()
        self.retry_attempts = 3
        self.backoff_multiplier = 2
        
        print(f"🛡️ GTI Rate Limiter initialized")
        print(f"   Min delay: {self.min_delay}s")
        print(f"   Base delay: {self.base_delay}s")
        print(f"   Max delay: {self.max_delay}s")
        print(f"   Retry attempts: {self.retry_attempts}")
    
    def wait_if_needed(self):
        """
        Chờ nếu cần thiết để tránh rate limiting
        """
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.current_delay:
                sleep_time = self.current_delay - time_since_last
                print(f"🛡️ Rate limiting protection: waiting {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()
    
    def increase_delay(self):
        """
        Tăng delay khi gặp rate limit
        """
        with self.lock:
            self.current_delay = min(self.current_delay * self.backoff_multiplier, self.max_delay)
            print(f"🛡️ Increased delay to {self.current_delay:.2f}s due to rate limiting")
    
    def decrease_delay(self):
        """
        Giảm delay khi requests thành công
        """
        with self.lock:
            self.current_delay = max(self.current_delay * 0.8, self.base_delay)
    
    def reset_delay(self):
        """
        Reset delay về mức cơ bản
        """
        with self.lock:
            self.current_delay = self.base_delay
            print(f"🛡️ Reset delay to {self.base_delay}s")

# Global rate limiter instance
rate_limiter = GTIRateLimiter()

def rate_limited_call(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper để thực hiện function call với rate limiting protection
    """
    for attempt in range(rate_limiter.retry_attempts):
        try:
            # Wait before making request
            rate_limiter.wait_if_needed()
            
            # Make the actual call
            result = func(*args, **kwargs)
            
            # Success - gradually decrease delay
            if attempt == 0:  # First attempt success
                rate_limiter.decrease_delay()
            
            return result
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if it's a rate limit error
            if "rate" in error_str or "limit" in error_str or "quota" in error_str:
                print(f"🛡️ Rate limit detected on attempt {attempt + 1}: {str(e)}")
                
                # Increase delay for future requests
                rate_limiter.increase_delay()
                
                if attempt < rate_limiter.retry_attempts - 1:
                    # Wait longer before retry (with some randomness)
                    wait_time = (2 ** attempt) * 5 + random.uniform(0, 3)
                    print(f"🛡️ Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"🛡️ Max retries reached, giving up")
                    raise
            else:
                # Non-rate-limit error, don't retry
                raise
    
    return None

def rate_limited_vnstock_call(func: Callable, *args, **kwargs) -> Any:
    """
    Specific wrapper cho vnstock API calls
    """
    return rate_limited_call(func, *args, **kwargs)

def batch_rate_limited_calls(func_list: list, max_concurrent: int = 5) -> list:
    """
    Thực hiện batch calls với rate limiting
    """
    results = []
    
    # Process in smaller batches
    for i in range(0, len(func_list), max_concurrent):
        batch = func_list[i:i + max_concurrent]
        batch_results = []
        
        print(f"🛡️ Processing batch {i//max_concurrent + 1}: {len(batch)} calls")
        
        for func_call in batch:
            func, args, kwargs = func_call
            try:
                result = rate_limited_call(func, *args, **kwargs)
                batch_results.append(result)
            except Exception as e:
                print(f"🛡️ Batch call failed: {str(e)}")
                batch_results.append(None)
            
            # Small delay between calls in the same batch
            time.sleep(0.2)
        
        results.extend(batch_results)
        
        # Longer delay between batches
        if i + max_concurrent < len(func_list):
            print(f"🛡️ Batch completed, waiting before next batch...")
            time.sleep(2.0)
    
    return results

# Decorator for automatic rate limiting
def rate_limited(func):
    """
    Decorator để tự động áp dụng rate limiting
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return rate_limited_call(func, *args, **kwargs)
    return wrapper

# Test function
if __name__ == "__main__":
    print("🧪 Testing GTI Rate Limiter...")
    
    def mock_api_call(stock_symbol):
        """Mock API call for testing"""
        print(f"📡 Mock API call for {stock_symbol}")
        time.sleep(0.1)  # Simulate API call time
        return f"Data for {stock_symbol}"
    
    # Test rate limiting
    test_stocks = ["FPT", "VIC", "VCB", "HPG", "BID"]
    
    start_time = time.time()
    for stock in test_stocks:
        result = rate_limited_call(mock_api_call, stock)
        print(f"   Result: {result}")
    
    total_time = time.time() - start_time
    print(f"✅ Test completed in {total_time:.2f}s")
    print(f"📊 Average time per call: {total_time/len(test_stocks):.2f}s") 