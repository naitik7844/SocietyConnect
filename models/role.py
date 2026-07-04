from models.db import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))

    # Relationships
    users = db.relationship('User', back_populates='role', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }
