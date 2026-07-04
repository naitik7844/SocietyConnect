from models.db import db
from datetime import datetime

class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Plumbing, Electrical, Security, Cleaning, Other
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.id', ondelete='CASCADE'), nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    assigned_to_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, In Progress, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = db.Column(db.Text, nullable=True)

    # Relationships
    flat = db.relationship('Flat', back_populates='complaints')
    creator = db.relationship('User', foreign_keys=[created_by_user_id])
    assigned_staff = db.relationship('Staff', back_populates='assigned_complaints')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'flat_id': self.flat_id,
            'flat_number': self.flat.flat_number if self.flat else '',
            'building_name': self.flat.building.name if self.flat and self.flat.building else '',
            'created_by_username': self.creator.username if self.creator else '',
            'created_by_user_id': self.created_by_user_id,
            'assigned_staff_name': self.assigned_staff.user.username if self.assigned_staff and self.assigned_staff.user else 'Unassigned',
            'assigned_to_staff_id': self.assigned_to_staff_id,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'resolution_notes': self.resolution_notes
        }
