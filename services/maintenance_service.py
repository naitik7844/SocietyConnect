from models import db, Maintenance, Flat, Building
from datetime import datetime, date

class MaintenanceService:
    @staticmethod
    def get_all_bills():
        return Maintenance.query.order_by(Maintenance.due_date.desc()).all()

    @staticmethod
    def get_bills_by_flat(flat_id):
        return Maintenance.query.filter_by(flat_id=flat_id).order_by(Maintenance.due_date.desc()).all()

    @staticmethod
    def get_bill_by_id(bill_id):
        return Maintenance.query.get(bill_id)

    @staticmethod
    def generate_bill(flat_id, title, amount, due_date, bill_date=None):
        if not bill_date:
            bill_date = datetime.utcnow().date()
        try:
            bill = Maintenance(
                flat_id=flat_id,
                title=title,
                amount=amount,
                due_date=due_date,
                bill_date=bill_date,
                status='Unpaid'
            )
            db.session.add(bill)
            db.session.commit()
            return bill, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def generate_bulk_bills(building_id, title, amount, due_date):
        try:
            flats = Flat.query.filter_by(building_id=building_id).all()
            bill_date = datetime.utcnow().date()
            bills_created = 0
            for flat in flats:
                # Only bill occupied flats
                if flat.occupancy_status != 'Vacant':
                    bill = Maintenance(
                        flat_id=flat.id,
                        title=title,
                        amount=amount,
                        due_date=due_date,
                        bill_date=bill_date,
                        status='Unpaid'
                    )
                    db.session.add(bill)
                    bills_created += 1
            db.session.commit()
            return bills_created, None
        except Exception as e:
            db.session.rollback()
            return 0, str(e)
