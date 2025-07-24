import logging
from google.protobuf.message import Message
from google.protobuf.json_format import MessageToJson, Parse
from proto.game_pb2 import PlayerInfo, LikeRequest, LikeResponse

logger = logging.getLogger(__name__)

class ProtobufHandler:
    """Handle protobuf message serialization and deserialization for Free Fire API"""
    
    @staticmethod
    def create_player_info_request(uid, server_name):
        """
        Create a player info request protobuf message
        
        Args:
            uid (str): Player UID
            server_name (str): Server name
        
        Returns:
            bytes: Serialized protobuf message
        """
        try:
            # Create PlayerInfo request
            request = PlayerInfo()
            request.uid = uid
            request.server = server_name
            
            # Serialize to bytes
            serialized = request.SerializeToString()
            logger.debug(f"Created PlayerInfo request for UID: {uid}")
            return serialized
            
        except Exception as e:
            logger.error(f"Error creating PlayerInfo request: {e}")
            raise
    
    @staticmethod
    def create_like_request(target_uid, sender_uid, server_name):
        """
        Create a like request protobuf message
        
        Args:
            target_uid (str): UID of player to like
            sender_uid (str): UID of sender
            server_name (str): Server name
        
        Returns:
            bytes: Serialized protobuf message
        """
        try:
            # Create LikeRequest
            request = LikeRequest()
            request.target_uid = target_uid
            request.sender_uid = sender_uid
            request.server = server_name
            
            # Serialize to bytes
            serialized = request.SerializeToString()
            logger.debug(f"Created LikeRequest for target: {target_uid}")
            return serialized
            
        except Exception as e:
            logger.error(f"Error creating LikeRequest: {e}")
            raise
    
    @staticmethod
    def parse_player_info_response(data):
        """
        Parse player info response from protobuf data
        
        Args:
            data (bytes): Serialized protobuf response
        
        Returns:
            PlayerInfo: Parsed player info message
        """
        try:
            response = PlayerInfo()
            response.ParseFromString(data)
            logger.debug("Parsed PlayerInfo response")
            return response
            
        except Exception as e:
            logger.error(f"Error parsing PlayerInfo response: {e}")
            raise
    
    @staticmethod
    def parse_like_response(data):
        """
        Parse like response from protobuf data
        
        Args:
            data (bytes): Serialized protobuf response
        
        Returns:
            LikeResponse: Parsed like response message
        """
        try:
            response = LikeResponse()
            response.ParseFromString(data)
            logger.debug("Parsed LikeResponse")
            return response
            
        except Exception as e:
            logger.error(f"Error parsing LikeResponse: {e}")
            raise
    
    @staticmethod
    def message_to_dict(message):
        """
        Convert protobuf message to dictionary
        
        Args:
            message (Message): Protobuf message
        
        Returns:
            dict: Message as dictionary
        """
        try:
            json_str = MessageToJson(message)
            import json
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error converting message to dict: {e}")
            raise

# Global protobuf handler instance
protobuf_handler = ProtobufHandler()
