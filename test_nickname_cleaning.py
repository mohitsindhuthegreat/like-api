#!/usr/bin/env python3
"""
Test script to demonstrate improved nickname cleaning with Unicode characters
"""

from real_token_generator import real_token_generator

def test_nickname_cleaning():
    """Test various problematic nicknames"""
    
    test_cases = [
        # User's specific example
        ('\u13eb\u13ae_\u13a1\u00f8\u043dI\u2ca7\u0fd0', 'User example with Cherokee/Cyrillic'),
        
        # Other common gaming nickname patterns
        ('\u13A0\u13A1\u13A2_Player', 'Cherokee letters'),
        ('\u043F\u0440\u0438\u0432\u0435\u0442', 'Cyrillic text'),
        ('\u1d22\u1d0f\u1d0f\u029f', 'Small caps'),
        ('Pro\u00f8Gamer\u2764\ufe0f', 'Mixed special characters'),
        ('', 'Empty string'),
        ('ABC123', 'Normal ASCII'),
        ('\u3164\u200b\u200c', 'Only invisible characters'),
        ('\u13eb\u13ae\u13a1\u043d\u2ca7', 'Mixed Unicode blocks'),
        ('Fire\u1d22\u1d0f\u1d0f\u029f_Player', 'Mixed ASCII and Unicode'),
    ]
    
    print("🎮 Free Fire Nickname Cleaning Test")
    print("=" * 50)
    
    for nickname, description in test_cases:
        try:
            cleaned = real_token_generator.clean_nickname(nickname)
            print(f"\n📝 {description}")
            print(f"   Original: {repr(nickname)} → {nickname if nickname else '(empty)'}")
            print(f"   Cleaned:  {repr(cleaned)} → {cleaned}")
            print(f"   Length:   {len(nickname)} → {len(cleaned)}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Nickname cleaning test completed!")

if __name__ == "__main__":
    test_nickname_cleaning()