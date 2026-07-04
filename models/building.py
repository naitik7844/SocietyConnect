from models.db import db

class Building(db.Model):
    __tablename__ = 'buildings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(255))
    floors_count = db.Column(db.Integer, default=1)

    # Relationships
    flats = db.relationship('Flat', back_populates='building', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'floors_count': self.floors_count
        }
