from models.db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='RESTRICT'), nullable=False)
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    role = db.relationship('Role', back_populates='users')
    resident = db.relationship('Resident', uselist=False, back_populates='user', cascade='all, delete-orphan')
    staff = db.relationship('Staff', uselist=False, back_populates='user', cascade='all, delete-orphan')
    created_notices = db.relationship('Notice', back_populates='creator', lazy=True)
    created_events = db.relationship('Event', back_populates='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role.name == 'Admin'

    @property
    def is_security(self):
        return self.role.name == 'Security'

    @property
    def is_resident(self):
        return self.role.name in ['Resident', 'Owner']

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'role': self.role.name if self.role else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
