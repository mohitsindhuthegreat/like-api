from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class PlayerRecord(db.Model):
    __tablename__ = 'player_records'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.BigInteger, nullable=False, index=True)
    nickname = db.Column(db.Text, nullable=True)  # Using Text for Unicode support
    server_name = db.Column(db.String(10), nullable=False)
    likes_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Add unique constraint for UID + Server combination
    __table_args__ = (
        db.UniqueConstraint('uid', 'server_name', name='uid_server_unique'),
    )
    
    def __repr__(self):
        return f'<PlayerRecord {self.uid}: {self.nickname}>'
    
    def to_dict(self):
        return {
            'uid': self.uid,
            'nickname': self.nickname,
            'server_name': self.server_name,
            'likes_count': self.likes_count,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }