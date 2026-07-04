from models.db import db
from datetime import datetime

class Resident(db.Model):
    __tablename__ = 'residents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.id', ondelete='CASCADE'), nullable=True)
    resident_type = db.Column(db.String(50), nullable=False, default='Tenant')  # Owner, Tenant
    emergency_contact = db.Column(db.String(100))
    move_in_date = db.Column(db.Date, default=datetime.utcnow().date)

    # Relationships
    user = db.relationship('User', back_populates='resident')
    flat = db.relationship('Flat', back_populates='residents')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '',
            'email': self.user.email if self.user else '',
            'phone': self.user.phone if self.user else '',
            'flat_id': self.flat_id,
            'flat_number': self.flat.flat_number if self.flat else '',
            'building_name': self.flat.building.name if self.flat and self.flat.building else '',
            'resident_type': self.resident_type,
            'emergency_contact': self.emergency_contact,
            'move_in_date': self.move_in_date.strftime('%Y-%m-%d') if self.move_in_date else None
        }
