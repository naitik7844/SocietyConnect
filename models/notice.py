from models.db import db
from datetime import datetime

class Notice(db.Model):
    __tablename__ = 'notices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.Date, nullable=True)
    attachment_path = db.Column(db.String(255), nullable=True)

    # Relationships
    creator = db.relationship('User', back_populates='created_notices')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_by_username': self.creator.username if self.creator else 'Admin',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'attachment_path': self.attachment_path
        }
