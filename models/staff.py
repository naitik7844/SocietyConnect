from models.db import db
from datetime import datetime

class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    staff_type = db.Column(db.String(50), nullable=False)  # Security, Maintenance, Admin, Other
    designation = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    joining_date = db.Column(db.Date, default=datetime.utcnow().date)

    # Relationships
    user = db.relationship('User', back_populates='staff')
    assigned_complaints = db.relationship('Complaint', back_populates='assigned_staff', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'email': self.user.email if self.user else '',
            'phone': self.user.phone if self.user else '',
            'staff_type': self.staff_type,
            'designation': self.designation,
            'salary': float(self.salary) if self.salary else 0.0,
            'joining_date': self.joining_date.strftime('%Y-%m-%d') if self.joining_date else None
        }
