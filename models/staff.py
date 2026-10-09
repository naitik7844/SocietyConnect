from models.db import db
from datetime import datetime
import re

class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)
    full_name = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(50), nullable=True)  # Plumbing, Electrical, Security, Cleaning, Other / General
    staff_type = db.Column(db.String(50), nullable=False, default='Maintenance')  # Security, Maintenance, Admin, Other
    designation = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    joining_date = db.Column(db.Date, default=datetime.utcnow().date)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='staff')
    assigned_complaints = db.relationship('Complaint', foreign_keys='Complaint.assigned_to_staff_id', back_populates='assigned_staff', lazy=True)

    @property
    def name(self):
        return self.full_name or (self.user.username if self.user else f"Staff #{self.id}")

    @property
    def contact_phone(self):
        return self.phone or (self.user.phone if self.user else '')

    @property
    def tel_link(self):
        num = re.sub(r'[^\d+]', '', self.contact_phone or '')
        return f"tel:{num}" if num else "#"

    @property
    def whatsapp_link(self):
        digits = re.sub(r'[^\d]', '', self.contact_phone or '')
        if not digits:
            return "#"
        if len(digits) == 10:
            digits = f"91{digits}"
        return f"https://wa.me/{digits}"

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'full_name': self.full_name,
            'username': self.user.username if self.user else '',
            'email': self.user.email if self.user else '',
            'phone': self.contact_phone,
            'department': self.department,
            'staff_type': self.staff_type,
            'designation': self.designation,
            'salary': float(self.salary) if self.salary else 0.0,
            'joining_date': self.joining_date.strftime('%Y-%m-%d') if self.joining_date else None,
            'is_active': self.is_active,
            'tel_link': self.tel_link,
            'whatsapp_link': self.whatsapp_link
        }
