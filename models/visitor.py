from models.db import db
from datetime import datetime

class Visitor(db.Model):
    __tablename__ = 'visitors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    purpose = db.Column(db.String(255), nullable=False)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.id', ondelete='CASCADE'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    vehicle_number = db.Column(db.String(20))
    status = db.Column(db.String(50), default='Checked-In')  # Checked-In, Checked-Out
    checked_in_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    flat = db.relationship('Flat', back_populates='visitors')
    security_user = db.relationship('User', foreign_keys=[checked_in_by])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'purpose': self.purpose,
            'flat_id': self.flat_id,
            'flat_number': self.flat.flat_number if self.flat else '',
            'building_name': self.flat.building.name if self.flat and self.flat.building else '',
            'check_in_time': self.check_in_time.strftime('%Y-%m-%d %H:%M:%S') if self.check_in_time else None,
            'check_out_time': self.check_out_time.strftime('%Y-%m-%d %H:%M:%S') if self.check_out_time else None,
            'vehicle_number': self.vehicle_number,
            'status': self.status,
            'checked_in_by_username': self.security_user.username if self.security_user else 'System'
        }
