from app import db
from datetime import datetime

class PlayerRecord(db.Model):
    __tablename__ = 'player_records'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(20), nullable=False, index=True)
    nickname = db.Column(db.String(100), nullable=False)
    server_name = db.Column(db.String(10), nullable=False, index=True)
    likes_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Create composite index for faster queries
    __table_args__ = (
        db.Index('idx_uid_server', 'uid', 'server_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'nickname': self.nickname,
            'server_name': self.server_name,
            'likes_count': self.likes_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
    def __repr__(self):
        return f'<PlayerRecord {self.uid}: {self.nickname}>'

class TokenRecord(db.Model):
    __tablename__ = 'token_records'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(20), nullable=False, index=True)
    server_name = db.Column(db.String(10), nullable=False, index=True)
    token = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Create composite index for faster queries
    __table_args__ = (
        db.Index('idx_uid_server_token', 'uid', 'server_name', 'is_active'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'server_name': self.server_name,
            'token': self.token,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'is_active': self.is_active
        }
        
    def __repr__(self):
        return f'<TokenRecord {self.uid} - {self.server_name}>'

# Tables will be created by main app