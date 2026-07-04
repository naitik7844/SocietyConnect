from models import db, Payment, Maintenance
from datetime import datetime
import uuid

class PaymentService:
    @staticmethod
    def get_all_payments():
        return Payment.query.order_by(Payment.payment_date.desc()).all()

    @staticmethod
    def get_payments_by_flat(flat_id):
        return Payment.query.join(Maintenance).filter(Maintenance.flat_id == flat_id).order_by(Payment.payment_date.desc()).all()

    @staticmethod
    def process_payment(maintenance_id, payment_method, amount_paid, transaction_id=None):
        bill = Maintenance.query.get(maintenance_id)
        if not bill:
            return None, "Maintenance bill not found"
        
        if bill.status == 'Paid':
            return None, "This maintenance bill is already paid"

        if not transaction_id:
            # Generate dummy transaction ID if not provided
            transaction_id = "TXN-" + str(uuid.uuid4().hex[:12]).upper()

        try:
            payment = Payment(
                maintenance_id=maintenance_id,
                amount_paid=amount_paid,
                payment_method=payment_method,
                transaction_id=transaction_id,
                status='Success',
                payment_date=datetime.utcnow()
            )
            db.session.add(payment)
            
            # Update bill status
            bill.status = 'Paid'
            
            db.session.commit()
            return payment, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
