from models import db, Complaint, Staff

class ComplaintService:
    @staticmethod
    def get_all_complaints():
        return Complaint.query.order_by(Complaint.created_at.desc()).all()

    @staticmethod
    def get_complaints_by_user(user_id):
        return Complaint.query.filter_by(created_by_user_id=user_id).order_by(Complaint.created_at.desc()).all()

    @staticmethod
    def get_complaint_by_id(complaint_id):
        return Complaint.query.get(complaint_id)

    @staticmethod
    def file_complaint(title, description, category, flat_id, created_by_user_id):
        try:
            complaint = Complaint(
                title=title,
                description=description,
                category=category,
                flat_id=flat_id,
                created_by_user_id=created_by_user_id,
                status='Pending'
            )
            db.session.add(complaint)
            db.session.commit()
            return complaint, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def assign_complaint(complaint_id, staff_id):
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found"
        try:
            complaint.assigned_to_staff_id = staff_id
            complaint.status = 'In Progress'
            db.session.commit()
            return True, "Complaint assigned successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def resolve_complaint(complaint_id, resolution_notes):
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found"
        try:
            complaint.resolution_notes = resolution_notes
            complaint.status = 'Resolved'
            db.session.commit()
            return True, "Complaint resolved successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e)
            
    @staticmethod
    def get_maintenance_staff():
        return Staff.query.filter(Staff.staff_type.in_(['Maintenance', 'Other'])).all()
