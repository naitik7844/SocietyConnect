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
    assigned_at = db.Column(db.DateTime, nullable=True)
    assigned_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Assigned, In Progress, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_notes = db.Column(db.Text, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    flat = db.relationship('Flat', back_populates='complaints')
    creator = db.relationship('User', foreign_keys=[created_by_user_id])
    assigned_staff = db.relationship('Staff', foreign_keys=[assigned_to_staff_id], back_populates='assigned_complaints')
    assigned_by = db.relationship('User', foreign_keys=[assigned_by_user_id])
    resolved_by = db.relationship('User', foreign_keys=[resolved_by_user_id])
    history = db.relationship('ComplaintHistory', back_populates='complaint', order_by='ComplaintHistory.created_at.desc()', cascade='all, delete-orphan', lazy=True)

    @property
    def reference_timestamp(self):
        """
        Determines the relevant starting timestamp for measuring elapsed time:
        - Reopened: when the complaint was reopened (or updated_at fallback)
        - Assigned / In Progress: when the staff was assigned (or created_at fallback)
        - Pending: when the complaint was created
        - Resolved: resolved_at
        """
        if self.status == 'Reopened':
            if self.history:
                reopened_entry = next((h for h in self.history if h.action == 'Reopened'), None)
                if reopened_entry and reopened_entry.created_at:
                    return reopened_entry.created_at
            return self.updated_at or self.created_at
        elif self.status in ['Assigned', 'In Progress']:
            return self.assigned_at or self.created_at
        elif self.status == 'Resolved':
            return self.resolved_at or self.updated_at or self.created_at
        return self.created_at

    @property
    def elapsed_seconds(self):
        if self.status == 'Resolved':
            return 0.0
        ref = self.reference_timestamp
        if not ref:
            return 0.0
        now = datetime.utcnow()
        return max(0.0, (now - ref).total_seconds())

    @property
    def is_overdue(self):
        if self.status == 'Resolved':
            return False
        try:
            from flask import current_app
            threshold_hours = current_app.config.get('COMPLAINT_OVERDUE_HOURS', 24)
        except Exception:
            threshold_hours = 24
        return self.elapsed_seconds >= (threshold_hours * 3600)

    @property
    def elapsed_time_formatted(self):
        secs = int(self.elapsed_seconds)
        if secs < 60:
            return "Just now"
        mins = secs // 60
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        remaining_mins = mins % 60
        if hours < 24:
            return f"{hours}h {remaining_mins}m"
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}d {remaining_hours}h"

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
            'assigned_staff_name': self.assigned_staff.name if self.assigned_staff else 'Unassigned',
            'assigned_to_staff_id': self.assigned_to_staff_id,
            'assigned_at': self.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if self.assigned_at else None,
            'assigned_by_username': self.assigned_by.username if self.assigned_by else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'resolution_notes': self.resolution_notes,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'resolved_by_username': self.resolved_by.username if self.resolved_by else None,
            'is_overdue': self.is_overdue,
            'elapsed_time_formatted': self.elapsed_time_formatted,
            'elapsed_seconds': int(self.elapsed_seconds)
        }
