"""
Advanced Nickname Processing System
Handles all Unicode characters properly for Free Fire game nicknames
"""

import unicodedata
import re
import logging
from typing import Optional, Union

class NicknameProcessor:
    """Advanced Unicode nickname processor for Free Fire game data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def process_raw_nickname(self, raw_data: Union[str, bytes, None], uid: int) -> str:
        """
        Process raw nickname data from protobuf response
        Returns clean, displayable Unicode nickname
        """
        try:
            if not raw_data:
                return f"Player_{uid}"
            
            # Step 1: Convert to proper string format
            nickname = self._convert_to_string(raw_data)
            
            # Step 2: Handle Unicode normalization
            nickname = self._normalize_unicode(nickname)
            
            # Step 3: Clean problematic characters while preserving Unicode
            nickname = self._clean_nickname(nickname)
            
            # Step 4: Validate final result
            nickname = self._validate_nickname(nickname, uid)
            
            self.logger.info(f"✅ Processed nickname for UID {uid}: {repr(raw_data)} -> {repr(nickname)}")
            return nickname
            
        except Exception as e:
            self.logger.error(f"❌ Nickname processing failed for UID {uid}: {e}")
            return f"Player_{uid}"
    
    def _convert_to_string(self, raw_data: Union[str, bytes, None]) -> str:
        """Convert raw data to proper Unicode string"""
        if isinstance(raw_data, str):
            return raw_data
        
        if isinstance(raw_data, bytes):
            # Try multiple encodings for proper decoding
            encodings = ['utf-8', 'utf-16le', 'utf-16be', 'latin1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    decoded = raw_data.decode(encoding)
                    # Validate the decoded string contains printable characters
                    if any(ord(c) > 31 and ord(c) != 127 for c in decoded):
                        return decoded
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            # Fallback with error handling
            return raw_data.decode('utf-8', errors='replace')
        
        return str(raw_data)
    
    def _normalize_unicode(self, nickname: str) -> str:
        """Normalize Unicode characters to standard form"""
        try:
            # Use NFC normalization for consistent character representation
            normalized = unicodedata.normalize('NFC', nickname)
            return normalized
        except Exception:
            return nickname
    
    def _clean_nickname(self, nickname: str) -> str:
        """Clean nickname while preserving all visible Unicode characters"""
        # Remove only actual control characters, not Unicode symbols
        # Keep all printable Unicode including emojis, symbols, and special characters
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', nickname)
        
        # Remove excessive whitespace but preserve single spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _validate_nickname(self, nickname: str, uid: int) -> str:
        """Validate and provide fallback if needed"""
        if not nickname or len(nickname.strip()) == 0:
            return f"Player_{uid}"
        
        # Check if nickname has any meaningful content
        if all(ord(c) < 32 or ord(c) == 127 for c in nickname):
            return f"Player_{uid}"
        
        return nickname
    
    def get_display_info(self, nickname: str) -> dict:
        """Get detailed information about nickname for debugging"""
        return {
            'nickname': nickname,
            'length': len(nickname),
            'unicode_categories': list(set(unicodedata.category(c) for c in nickname)),
            'contains_emoji': any('\U0001F600' <= c <= '\U0001F64F' or 
                                '\U0001F300' <= c <= '\U0001F5FF' or
                                '\U0001F680' <= c <= '\U0001F6FF' or
                                '\U0001F1E0' <= c <= '\U0001F1FF' for c in nickname),
            'char_codes': [ord(c) for c in nickname[:10]]  # First 10 chars for debugging
        }

# Global instance
nickname_processor = NicknameProcessor()