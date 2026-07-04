from models.db import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    creator = db.relationship('User', back_populates='created_events')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'event_date': self.event_date.strftime('%Y-%m-%d %H:%M') if self.event_date else None,
            'venue': self.venue,
            'created_by_username': self.creator.username if self.creator else 'Admin',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
