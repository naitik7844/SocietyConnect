from models.db import db

class Flat(db.Model):
    __tablename__ = 'flats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id', ondelete='CASCADE'), nullable=False)
    flat_number = db.Column(db.String(20), nullable=False)
    floor_number = db.Column(db.Integer, nullable=False)
    flat_type = db.Column(db.String(50), default='2BHK')
    occupancy_status = db.Column(db.String(50), default='Vacant')

    # Relationships
    building = db.relationship('Building', back_populates='flats')
    residents = db.relationship('Resident', back_populates='flat', cascade='all, delete-orphan', lazy=True)
    visitors = db.relationship('Visitor', back_populates='flat', cascade='all, delete-orphan', lazy=True)
    complaints = db.relationship('Complaint', back_populates='flat', cascade='all, delete-orphan', lazy=True)
    maintenance_bills = db.relationship('Maintenance', back_populates='flat', cascade='all, delete-orphan', lazy=True)
    vehicles = db.relationship('Vehicle', back_populates='flat', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'building_id': self.building_id,
            'building_name': self.building.name if self.building else '',
            'flat_number': self.flat_number,
            'floor_number': self.floor_number,
            'flat_type': self.flat_type,
            'occupancy_status': self.occupancy_status
        }
