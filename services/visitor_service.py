from models import db, Visitor, Flat
from datetime import datetime
from utils.validators import validate_phone

class VisitorService:
    @staticmethod
    def get_all_visitors():
        return Visitor.query.order_by(Visitor.check_in_time.desc()).all()

    @staticmethod
    def get_active_visitors():
        return Visitor.query.filter_by(status='Checked-In').order_by(Visitor.check_in_time.desc()).all()

    @staticmethod
    def log_visitor_entry(name, phone, purpose, flat_id, vehicle_number=None, checked_in_by=None):
        # Check if phone number is valid
        if not validate_phone(phone):
            return None, "Invalid phone number. Must include a country code and 10 digits."

        try:
            visitor = Visitor(
                name=name,
                phone=phone,
                purpose=purpose,
                flat_id=flat_id,
                vehicle_number=vehicle_number,
                status='Checked-In',
                check_in_time=datetime.utcnow(),
                checked_in_by=checked_in_by
            )
            db.session.add(visitor)
            db.session.commit()
            return visitor, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def log_visitor_checkout(visitor_id):
        visitor = Visitor.query.get(visitor_id)
        if not visitor:
            return False, "Visitor not found"
        try:
            visitor.check_out_time = datetime.utcnow()
            visitor.status = 'Checked-Out'
            db.session.commit()
            return True, "Visitor checked out successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
            
    @staticmethod
    def get_visitors_by_flat(flat_id):
        return Visitor.query.filter_by(flat_id=flat_id).order_by(Visitor.check_in_time.desc()).all()
