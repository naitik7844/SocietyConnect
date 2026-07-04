from models.db import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    maintenance_id = db.Column(db.Integer, db.ForeignKey('maintenance.id', ondelete='CASCADE'), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), nullable=False)  # Card, Cash, UPI, NetBanking
    transaction_id = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50), default='Success')  # Success, Failed, Pending

    # Relationships
    maintenance_bill = db.relationship('Maintenance', back_populates='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'maintenance_id': self.maintenance_id,
            'bill_title': self.maintenance_bill.title if self.maintenance_bill else '',
            'flat_number': self.maintenance_bill.flat.flat_number if self.maintenance_bill and self.maintenance_bill.flat else '',
            'amount_paid': float(self.amount_paid),
            'payment_date': self.payment_date.strftime('%Y-%m-%d %H:%M:%S') if self.payment_date else None,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'status': self.status
        }
