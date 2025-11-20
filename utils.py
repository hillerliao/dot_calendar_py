import os
import json
import time
from typing import Any, Optional

class W2FileCache:
    """File-based cache implementation similar to the PHP version"""
    
    CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache')
    
    @classmethod
    def get_valid_data_from_file(cls, cache_file: str) -> Optional[Any]:
        """Retrieve valid data from cache file"""
        if not os.path.exists(cache_file):
            return None
            
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
                item = json.loads(content)
                
            if isinstance(item, dict) and (item.get('timeout') == 0 or 
                                          item.get('timeout') + item.get('update_time', 0) > time.time()):
                return item.get('data')
            return None
        except (IOError, json.JSONDecodeError):
            return None
    
    @classmethod
    def is_key_exist(cls, key: str) -> bool:
        """Check if cache key exists"""
        cache_file = os.path.join(cls.CACHE_PATH, f"{key}.cache")
        return os.path.exists(cache_file)
    
    @classmethod
    def get_cache(cls, key: str) -> Optional[Any]:
        """Get cached data by key"""
        cache_file = os.path.join(cls.CACHE_PATH, f"{key}.cache")
        return cls.get_valid_data_from_file(cache_file)
    
    @classmethod
    def set_cache(cls, key: str, data: Any = None, timeout: int = 0) -> None:
        """Set cache data"""
        if not os.path.exists(cls.CACHE_PATH):
            os.makedirs(cls.CACHE_PATH)
            
        cache_file = os.path.join(cls.CACHE_PATH, f"{key}.cache")
        item = {
            'data': data,
            'key': key,
            'timeout': timeout,
            'update_time': time.time()
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(item, f, ensure_ascii=False)
        except IOError:
            pass  # Silent fail like in PHP version