from models.db import db
from datetime import datetime

class ComplaintHistory(db.Model):
    __tablename__ = 'complaint_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # Created, Assigned, Reassigned, Status Changed, Resolved
    previous_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='SET NULL'), nullable=True)
    previous_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=True)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    complaint = db.relationship('Complaint', back_populates='history')
    previous_staff = db.relationship('Staff', foreign_keys=[previous_staff_id])
    assigned_staff = db.relationship('Staff', foreign_keys=[assigned_staff_id])
    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'action': self.action,
            'previous_staff_name': self.previous_staff.name if self.previous_staff else None,
            'assigned_staff_name': self.assigned_staff.name if self.assigned_staff else None,
            'previous_status': self.previous_status,
            'new_status': self.new_status,
            'changed_by': self.changed_by.username if self.changed_by else 'System',
            'notes': self.notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
