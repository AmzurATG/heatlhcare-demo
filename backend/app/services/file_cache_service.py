import hashlib
import json
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileCacheService:
    """Service for caching processed file content to avoid reprocessing"""
    
    def __init__(self):
        # In-memory cache - in production, use Redis or database
        self.processed_files_cache: Dict[str, Dict[str, Any]] = {}
        self.file_summaries_cache: Dict[str, str] = {}
        self.cache_expiry_time = 3600  # 1 hour cache expiry
    
    def _generate_file_hash(self, file_content: bytes, filename: str) -> str:
        """Generate unique hash for file content and name"""
        content_hash = hashlib.md5(file_content).hexdigest()
        name_hash = hashlib.md5(filename.encode()).hexdigest()
        return f"{content_hash}_{name_hash}"
    
    def get_cached_file_analysis(self, file_content: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Get cached file analysis if available and not expired"""
        file_hash = self._generate_file_hash(file_content, filename)
        
        cached_data = self.processed_files_cache.get(file_hash)
        if not cached_data:
            return None
        
        # Check if cache is expired
        if time.time() - cached_data.get('cached_at', 0) > self.cache_expiry_time:
            del self.processed_files_cache[file_hash]
            return None
        
        logger.info(f"Cache HIT for file: {filename}")
        return cached_data.get('analysis')
    
    def cache_file_analysis(self, file_content: bytes, filename: str, analysis: Dict[str, Any]):
        """Cache file analysis result"""
        file_hash = self._generate_file_hash(file_content, filename)
        
        self.processed_files_cache[file_hash] = {
            'analysis': analysis,
            'cached_at': time.time(),
            'filename': filename,
            'file_size': len(file_content)
        }
        
        logger.info(f"Cache STORED for file: {filename}")
    
    def get_cached_summary(self, file_content: bytes, filename: str) -> Optional[str]:
        """Get cached file summary for chat context"""
        file_hash = self._generate_file_hash(file_content, filename)
        
        cached_summary = self.file_summaries_cache.get(file_hash)
        if cached_summary:
            logger.info(f"Summary cache HIT for file: {filename}")
            return cached_summary
        
        return None
    
    def cache_summary(self, file_content: bytes, filename: str, summary: str):
        """Cache file summary for quick retrieval"""
        file_hash = self._generate_file_hash(file_content, filename)
        self.file_summaries_cache[file_hash] = summary
        logger.info(f"Summary cache STORED for file: {filename}")
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for file_hash, cached_data in self.processed_files_cache.items():
            if current_time - cached_data.get('cached_at', 0) > self.cache_expiry_time:
                expired_keys.append(file_hash)
        
        for key in expired_keys:
            del self.processed_files_cache[key]
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "processed_files_count": len(self.processed_files_cache),
            "summaries_count": len(self.file_summaries_cache),
            "cache_size_mb": self._estimate_cache_size(),
            "expiry_time_hours": self.cache_expiry_time / 3600
        }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB"""
        try:
            # Rough estimation
            cache_str = json.dumps(self.processed_files_cache) + json.dumps(self.file_summaries_cache)
            return len(cache_str.encode()) / (1024 * 1024)
        except:
            return 0.0

# Global cache instance
file_cache_service = FileCacheService()
