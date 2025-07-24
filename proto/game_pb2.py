# Simple message classes for Free Fire API
# This replaces the complex protobuf implementation with basic Python classes

import json

class PlayerInfo:
    def __init__(self):
        self.uid = ""
        self.server = ""
        self.account_info = b""
        self.PlayerNickname = ""
        self.Likes = 0
        self.Avatar = ""
        self.AccountInfo = None

    def SerializeToString(self):
        # Simple JSON serialization for API compatibility
        data = {
            "uid": self.uid,
            "server": self.server,
            "account_info": self.account_info.decode('utf-8') if self.account_info else "",
            "PlayerNickname": self.PlayerNickname,
            "Likes": self.Likes,
            "Avatar": self.Avatar
        }
        return json.dumps(data).encode('utf-8')

    def ParseFromString(self, data):
        try:
            if isinstance(data, bytes):
                json_data = json.loads(data.decode('utf-8'))
            else:
                json_data = data
            
            self.uid = str(json_data.get("uid", ""))
            self.server = str(json_data.get("server", ""))
            self.PlayerNickname = str(json_data.get("PlayerNickname", ""))
            self.Likes = int(json_data.get("Likes", 0))
            self.Avatar = str(json_data.get("Avatar", ""))
            
            # Create AccountInfo object
            self.AccountInfo = AccountInfo()
            self.AccountInfo.UID = int(json_data.get("UID", 0))
            self.AccountInfo.PlayerNickname = self.PlayerNickname
            self.AccountInfo.Likes = self.Likes
            self.AccountInfo.Avatar = self.Avatar
            self.AccountInfo.Level = int(json_data.get("Level", 1))
            self.AccountInfo.Region = str(json_data.get("Region", ""))
            self.AccountInfo.LastLoginTime = int(json_data.get("LastLoginTime", 0))
            
        except Exception as e:
            print(f"Error parsing PlayerInfo: {e}")

class LikeRequest:
    def __init__(self):
        self.target_uid = ""
        self.sender_uid = ""
        self.server = ""
        self.id = 0

    def SerializeToString(self):
        data = {
            "target_uid": self.target_uid,
            "sender_uid": self.sender_uid,
            "server": self.server,
            "id": self.id
        }
        return json.dumps(data).encode('utf-8')

    def ParseFromString(self, data):
        try:
            if isinstance(data, bytes):
                json_data = json.loads(data.decode('utf-8'))
            else:
                json_data = data
            
            self.target_uid = str(json_data.get("target_uid", ""))
            self.sender_uid = str(json_data.get("sender_uid", ""))
            self.server = str(json_data.get("server", ""))
            self.id = int(json_data.get("id", 0))
        except Exception as e:
            print(f"Error parsing LikeRequest: {e}")

class LikeResponse:
    def __init__(self):
        self.success = False
        self.message = ""
        self.id = 0

    def SerializeToString(self):
        data = {
            "success": self.success,
            "message": self.message,
            "id": self.id
        }
        return json.dumps(data).encode('utf-8')

    def ParseFromString(self, data):
        try:
            if isinstance(data, bytes):
                json_data = json.loads(data.decode('utf-8'))
            else:
                json_data = data
            
            self.success = bool(json_data.get("success", False))
            self.message = str(json_data.get("message", ""))
            self.id = int(json_data.get("id", 0))
        except Exception as e:
            print(f"Error parsing LikeResponse: {e}")

class AccountInfo:
    def __init__(self):
        self.UID = 0
        self.PlayerNickname = ""
        self.Likes = 0
        self.Level = 1
        self.Avatar = ""
        self.Region = ""
        self.LastLoginTime = 0

    def SerializeToString(self):
        data = {
            "UID": self.UID,
            "PlayerNickname": self.PlayerNickname,
            "Likes": self.Likes,
            "Level": self.Level,
            "Avatar": self.Avatar,
            "Region": self.Region,
            "LastLoginTime": self.LastLoginTime
        }
        return json.dumps(data).encode('utf-8')

    def ParseFromString(self, data):
        try:
            if isinstance(data, bytes):
                json_data = json.loads(data.decode('utf-8'))
            else:
                json_data = data
            
            self.UID = int(json_data.get("UID", 0))
            self.PlayerNickname = str(json_data.get("PlayerNickname", ""))
            self.Likes = int(json_data.get("Likes", 0))
            self.Level = int(json_data.get("Level", 1))
            self.Avatar = str(json_data.get("Avatar", ""))
            self.Region = str(json_data.get("Region", ""))
            self.LastLoginTime = int(json_data.get("LastLoginTime", 0))
        except Exception as e:
            print(f"Error parsing AccountInfo: {e}")