from models.db import db

class Maintenance(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    bill_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), default='Unpaid')  # Unpaid, Paid, Overdue

    # Relationships
    flat = db.relationship('Flat', back_populates='maintenance_bills')
    payments = db.relationship('Payment', back_populates='maintenance_bill', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'flat_id': self.flat_id,
            'flat_number': self.flat.flat_number if self.flat else '',
            'building_name': self.flat.building.name if self.flat and self.flat.building else '',
            'title': self.title,
            'amount': float(self.amount),
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'bill_date': self.bill_date.strftime('%Y-%m-%d') if self.bill_date else None,
            'status': self.status
        }
