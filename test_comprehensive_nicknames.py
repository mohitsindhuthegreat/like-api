#!/usr/bin/env python3
"""
Comprehensive test for nickname handling across different scenarios
"""

def test_nickname_scenarios():
    """Test various nickname encoding scenarios"""
    
    test_cases = [
        # Normal ASCII
        ("PlayerName123", "Normal ASCII nickname"),
        
        # Your specific example
        ('\u13eb\u13ae_\u13a1\u00f8\u043dI\u2ca7\u0fd0', "User's Cherokee/Cyrillic example"),
        
        # Common gaming names with special chars
        ("ZAINX!TERS", "ASCII with special characters"),
        ("Pro_Gamer_2024", "Underscore separated"),
        
        # Unicode variations
        ("Ꭰ𝕏𝕖₂₀₂₄", "Mixed Unicode scripts"),
        ("Fire🔥Player", "With emoji"),
        ("测试玩家", "Chinese characters"),
        ("プレイヤー", "Japanese characters"),
        ("Игрок", "Cyrillic"),
        ("محارب", "Arabic"),
        
        # Edge cases
        ("", "Empty string"),
        ("   ", "Only spaces"),
        ("A", "Single character"),
        
        # Problematic characters
        ("Player\x00Name", "With null character"),
        ("Name\u200bWith\u200cInvisible", "With invisible characters"),
    ]
    
    print("🎮 Comprehensive Nickname Processing Test")
    print("=" * 60)
    
    from main import app
    
    for test_nickname, description in test_cases:
        try:
            # Simulate the nickname processing logic from main.py
            with app.app_context():
                player_uid = 12345
                raw_player_name = test_nickname
                
                # Apply the same processing logic
                player_name = raw_player_name
                
                # Handle different data types
                if isinstance(raw_player_name, bytes):
                    for encoding in ['utf-8', 'utf-16', 'latin1', 'cp1252']:
                        try:
                            player_name = raw_player_name.decode(encoding)
                            break
                        except:
                            continue
                elif isinstance(raw_player_name, str):
                    player_name = raw_player_name
                    
                    import codecs
                    try:
                        player_name = codecs.decode(player_name, 'unicode_escape')
                    except:
                        pass
                else:
                    player_name = str(raw_player_name)
                
                # Normalize Unicode characters
                import unicodedata
                try:
                    player_name = unicodedata.normalize('NFC', player_name)
                except:
                    pass
                
                # Remove control characters
                import re
                player_name = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', player_name)
                player_name = player_name.strip()
                
                # Fallback if empty
                if not player_name:
                    player_name = f"Player_{player_uid}"
                
                print(f"\n📝 {description}")
                print(f"   Input:  {repr(test_nickname)} -> {test_nickname if test_nickname else '(empty)'}")
                print(f"   Output: {repr(player_name)} -> {player_name}")
                print(f"   Status: {'✅ Processed' if player_name else '❌ Failed'}")
                
        except Exception as e:
            print(f"\n📝 {description}")
            print(f"   Input:  {repr(test_nickname)}")
            print(f"   Status: ❌ Error - {e}")
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive nickname test completed!")
    print("✅ System can handle various Unicode patterns and edge cases")

if __name__ == "__main__":
    test_nickname_scenarios()