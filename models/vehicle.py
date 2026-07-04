from models.db import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.id', ondelete='CASCADE'), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)  # 2 Wheeler, 4 Wheeler
    vehicle_number = db.Column(db.String(50), nullable=False, unique=True)
    owner_name = db.Column(db.String(100), nullable=False)

    # Relationships
    flat = db.relationship('Flat', back_populates='vehicles')

    def to_dict(self):
        return {
            'id': self.id,
            'flat_id': self.flat_id,
            'flat_number': self.flat.flat_number if self.flat else '',
            'building_name': self.flat.building.name if self.flat and self.flat.building else '',
            'vehicle_type': self.vehicle_type,
            'vehicle_number': self.vehicle_number,
            'owner_name': self.owner_name
        }
