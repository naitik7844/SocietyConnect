from models import db, Complaint, Staff, ComplaintHistory, Resident
from services.staff_service import StaffService, CATEGORY_TO_DEPARTMENT
from datetime import datetime

class ComplaintService:
    @staticmethod
    def get_all_complaints(status=None):
        if status == 'Overdue':
            # Derived overdue tracking: all non-resolved complaints exceeding overdue threshold
            complaints = Complaint.query.filter(Complaint.status != 'Resolved').order_by(Complaint.created_at.desc()).all()
            return [c for c in complaints if c.is_overdue]
        elif status:
            return Complaint.query.filter_by(status=status).order_by(Complaint.created_at.desc()).all()
        return Complaint.query.order_by(Complaint.created_at.desc()).all()

    @staticmethod
    def get_complaints_by_user(user_id, status=None):
        if status == 'Overdue':
            complaints = Complaint.query.filter_by(created_by_user_id=user_id).filter(Complaint.status != 'Resolved').order_by(Complaint.created_at.desc()).all()
            return [c for c in complaints if c.is_overdue]
        query = Complaint.query.filter_by(created_by_user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Complaint.created_at.desc()).all()

    @staticmethod
    def get_complaint_by_id(complaint_id):
        return Complaint.query.get(complaint_id)

    @staticmethod
    def can_user_view_complaint(complaint, user):
        """
        Enforces strict backend authorization checks:
        Only admin, creator, or authorized flat residents/owners may view.
        Unrelated residents are forbidden.
        """
        if not complaint or not user or not user.is_authenticated:
            return False

        if user.is_admin:
            return True

        if complaint.created_by_user_id == user.id:
            return True

        # Check if user is linked to the same flat as resident/owner
        resident = Resident.query.filter_by(user_id=user.id, flat_id=complaint.flat_id).first()
        if resident:
            return True

        return False

    @staticmethod
    def can_user_manage_complaint(complaint, user):
        """
        Determines whether the user is authorized to resolve or manage this complaint:
        - Admin can manage any complaint.
        - Creator of the complaint can manage it.
        - Resident/owner/tenant linked to the complaint's flat can manage it.
        """
        return ComplaintService.can_user_view_complaint(complaint, user)

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
            db.session.flush()

            # Record creation in history
            history_entry = ComplaintHistory(
                complaint_id=complaint.id,
                action='Created',
                previous_status=None,
                new_status='Pending',
                changed_by_user_id=created_by_user_id,
                notes=f"Complaint ticket filed under {category} category"
            )
            db.session.add(history_entry)
            db.session.commit()
            return complaint, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def assign_complaint(complaint_id, staff_id, admin_user_id=None):
        """
        Assigns or reassigns a complaint to an active, category-eligible staff member.
        Enforces category matching, prevents assigning inactive/nonexistent staff,
        preserves history, and updates timestamps and admin ID.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found."

        staff = Staff.query.get(staff_id)
        if not staff:
            return False, "Selected staff member does not exist."

        # 1. Active staff validation
        if not staff.is_active:
            return False, f"Staff member '{staff.name}' is marked as Inactive and cannot receive new assignments."

        # 2. Category compatibility validation
        eligible_staff = StaffService.get_staff_for_category(complaint.category)
        eligible_ids = [s.id for s in eligible_staff]
        if staff.id not in eligible_ids:
            dept_name = staff.department or staff.staff_type or 'General'
            return False, f"Staff member '{staff.name}' ({dept_name} - {staff.designation}) is not eligible for {complaint.category} complaints."

        previous_staff_id = complaint.assigned_to_staff_id
        previous_status = complaint.status

        # If already assigned to the same staff member
        if previous_staff_id == staff.id and previous_status in ['Assigned', 'In Progress']:
            return True, f"Complaint #{complaint.id} is already assigned to {staff.name}."

        is_reassignment = (previous_staff_id is not None and previous_staff_id != staff.id)

        try:
            complaint.assigned_to_staff_id = staff.id
            complaint.assigned_at = datetime.utcnow()
            if admin_user_id:
                complaint.assigned_by_user_id = admin_user_id

            # Update status: Pending or Reopened -> Assigned
            if previous_status in ['Pending', 'Reopened']:
                complaint.status = 'Assigned'
            # If already In Progress and reassigned, keep In Progress

            # Record in complaint history
            action_name = 'Reassigned' if is_reassignment else 'Assigned'
            notes = f"Assigned to {staff.name} ({staff.designation})"
            if is_reassignment:
                prev_staff = Staff.query.get(previous_staff_id)
                prev_name = prev_staff.name if prev_staff else f"Staff #{previous_staff_id}"
                notes = f"Reassigned from {prev_name} to {staff.name} ({staff.designation})"

            history_entry = ComplaintHistory(
                complaint_id=complaint.id,
                action=action_name,
                previous_staff_id=previous_staff_id,
                assigned_staff_id=staff.id,
                previous_status=previous_status,
                new_status=complaint.status,
                changed_by_user_id=admin_user_id,
                notes=notes
            )
            db.session.add(history_entry)
            db.session.commit()
            return True, f"Complaint assigned to {staff.name} successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error saving assignment: {str(e)}"

    @staticmethod
    def mark_in_progress(complaint_id, admin_user_id, notes=None):
        """
        Transitions complaint status from Assigned or Reopened to In Progress.
        Requires staff assignment first.
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found."

        if not complaint.assigned_to_staff_id:
            return False, "Complaint must be assigned to an authorized staff member before marking as In Progress."

        if complaint.status == 'In Progress':
            return True, "Complaint is already In Progress."

        if complaint.status == 'Resolved':
            return False, "Cannot set a resolved complaint to In Progress directly. Please use Reopen instead."

        try:
            previous_status = complaint.status
            complaint.status = 'In Progress'

            staff_name = complaint.assigned_staff.name if complaint.assigned_staff else "Assigned Staff"
            staff_desig = complaint.assigned_staff.designation if complaint.assigned_staff else ""
            default_notes = f"Work started on-site by {staff_name} ({staff_desig})." if staff_desig else f"Work started on-site by {staff_name}."

            history_entry = ComplaintHistory(
                complaint_id=complaint.id,
                action='In Progress',
                previous_staff_id=complaint.assigned_to_staff_id,
                assigned_staff_id=complaint.assigned_to_staff_id,
                previous_status=previous_status,
                new_status='In Progress',
                changed_by_user_id=admin_user_id,
                notes=notes.strip() if notes else default_notes
            )
            db.session.add(history_entry)
            db.session.commit()
            return True, f"Complaint #{complaint.id} marked as In Progress."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating status: {str(e)}"

    @staticmethod
    def resolve_complaint(complaint_id, resolution_notes=None, resolved_by_user_id=None):
        """
        Marks complaint as Resolved.
        Resolution notes are optional by default. If supplied, they are stored and preserved in history.
        Records completion timestamp and resolving actor (admin or resident).
        Can resolve directly from Assigned, In Progress, or Reopened (must have assigned staff).
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found."

        if complaint.status == 'Resolved':
            return False, "Complaint is already marked as resolved."

        if not complaint.assigned_to_staff_id:
            return False, "Cannot resolve an unassigned complaint. Assign staff first."

        notes_clean = (resolution_notes or '').strip()

        try:
            previous_status = complaint.status
            if notes_clean:
                complaint.resolution_notes = notes_clean

            complaint.status = 'Resolved'
            complaint.resolved_at = datetime.utcnow()
            complaint.resolved_by_user_id = resolved_by_user_id

            if notes_clean:
                history_note = notes_clean
            else:
                from models.user import User
                resolver_user = User.query.get(resolved_by_user_id) if resolved_by_user_id else None
                if resolver_user and resolver_user.is_admin:
                    history_note = "Resolved by administrator without additional notes."
                elif resolver_user:
                    history_note = f"Marked as resolved by {resolver_user.username}."
                else:
                    history_note = "Resolved without additional notes."

            history_entry = ComplaintHistory(
                complaint_id=complaint.id,
                action='Resolved',
                previous_staff_id=complaint.assigned_to_staff_id,
                assigned_staff_id=complaint.assigned_to_staff_id,
                previous_status=previous_status,
                new_status='Resolved',
                changed_by_user_id=resolved_by_user_id,
                notes=history_note
            )
            db.session.add(history_entry)
            db.session.commit()
            return True, "Complaint resolved successfully."
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def reopen_complaint(complaint_id, reason=None, user_id=None):
        """
        Reopens a resolved complaint if the resident/admin reports the issue persists.
        Transitions status from Resolved to Reopened (not In Progress).
        Preserves original resolved_at, resolver, resolution notes, and historical Resolved event.
        Reopening reason is optional.
        Preserves staff assignment unless staff is inactive (if inactive, unassigns for reassignment).
        """
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return False, "Complaint not found."

        if complaint.status != 'Resolved':
            return False, "Only resolved complaints can be reopened."

        reason_clean = (reason or '').strip()

        try:
            previous_status = complaint.status
            complaint.status = 'Reopened'

            inactive_staff_unassigned = False
            prev_staff_id = complaint.assigned_to_staff_id

            # If assigned staff is no longer active, unassign to flag for reassignment
            if complaint.assigned_staff and not complaint.assigned_staff.is_active:
                inactive_staff_unassigned = True
                complaint.assigned_to_staff_id = None
                complaint.assigned_at = None

            history_notes = f"Reopened by user: {reason_clean}" if reason_clean else "Complaint reopened."
            if inactive_staff_unassigned:
                history_notes += " Note: Previously assigned staff is inactive; ticket unassigned for reassignment."

            history_entry = ComplaintHistory(
                complaint_id=complaint.id,
                action='Reopened',
                previous_staff_id=prev_staff_id,
                assigned_staff_id=complaint.assigned_to_staff_id,
                previous_status=previous_status,
                new_status='Reopened',
                changed_by_user_id=user_id,
                notes=history_notes
            )
            db.session.add(history_entry)
            db.session.commit()
            return True, f"Complaint #{complaint.id} has been reopened."
        except Exception as e:
            db.session.rollback()
            return False, f"Error reopening complaint: {str(e)}"

    @staticmethod
    def get_staff_for_complaint(category):
        """
        Returns strictly category-eligible active staff.
        No fallback to unrelated staff when category has no personnel.
        """
        eligible = StaffService.get_staff_for_category(category)
        return {
            'eligible_staff': eligible,
            'has_eligible_staff': len(eligible) > 0,
            'category': category
        }
