from models import db, Staff, User, Complaint
from utils.validators import validate_phone
from datetime import datetime
import re

DEPARTMENT_DESIGNATIONS = {
    'Plumbing': ['Plumber', 'Senior Plumber'],
    'Electrical': ['Electrician', 'Senior Electrician'],
    'Security': ['Security Guard', 'Security Supervisor'],
    'Cleaning': ['Housekeeping Staff', 'Cleaning Supervisor'],
    'Other / General': ['General Maintenance Worker', 'Maintenance Technician']
}

CATEGORY_TO_DEPARTMENT = {
    'plumbing': 'Plumbing',
    'electrical': 'Electrical',
    'security': 'Security',
    'cleaning': 'Cleaning',
    'other': 'Other / General',
    'general': 'Other / General',
    'other / general': 'Other / General'
}

class StaffService:
    @staticmethod
    def get_all_staff():
        """Returns all staff records ordered by active status and id."""
        return Staff.query.order_by(Staff.is_active.desc(), Staff.id.asc()).all()

    @staticmethod
    def get_active_staff():
        """Returns active staff records only."""
        return Staff.query.filter_by(is_active=True).order_by(Staff.id.asc()).all()

    @staticmethod
    def get_staff_by_id(staff_id):
        return Staff.query.get(staff_id)

    @staticmethod
    def normalize_phone(phone, country_code='+91'):
        """Normalize phone number to international format."""
        if not phone:
            return None
        # Extract digits
        digits = re.sub(r'\D', '', str(phone))
        if len(digits) == 10:
            cc = country_code.strip() if country_code else '+91'
            if not cc.startswith('+'):
                cc = '+' + cc
            return f"{cc}{digits}"
        elif len(digits) > 10:
            return f"+{digits}"
        return phone.strip()

    @staticmethod
    def get_staff_for_category(category):
        """
        Returns active staff members eligible strictly for the specified complaint category.
        No fallback to unrelated staff.
        """
        if not category:
            return []

        cat_norm = category.strip().lower()
        target_dept = CATEGORY_TO_DEPARTMENT.get(cat_norm, 'Other / General')

        # Query all active staff
        active_staff = Staff.query.filter_by(is_active=True).all()
        eligible = []

        for s in active_staff:
            s_dept = s.department
            # Fallback deduction for legacy records without department
            if not s_dept:
                desig_lower = (s.designation or '').lower()
                stype_lower = (s.staff_type or '').lower()
                if 'plumb' in desig_lower:
                    s_dept = 'Plumbing'
                elif 'electr' in desig_lower:
                    s_dept = 'Electrical'
                elif 'security' in desig_lower or stype_lower == 'security':
                    s_dept = 'Security'
                elif 'clean' in desig_lower or 'housekeep' in desig_lower:
                    s_dept = 'Cleaning'
                else:
                    s_dept = 'Other / General'

            if s_dept == target_dept:
                eligible.append(s)

        return eligible

    @staticmethod
    def create_staff(full_name, phone, department, designation, salary=None, joining_date=None, country_code='+91'):
        """
        Registers a new authorized staff member with required and optional fields.
        Validates department and designation combinations.
        Does NOT create login credentials (username/email/password) as staff do not log in.
        """
        full_name = (full_name or '').strip()
        phone = (phone or '').strip()
        department = (department or '').strip()
        designation = (designation or '').strip()

        # 1. Required field validation
        if not full_name:
            return None, "Full Name is required."
        if len(full_name) < 2:
            return None, "Full Name must be at least 2 characters long."

        if not phone:
            return None, "Mobile Number is required."
        
        # Validate phone
        digits = re.sub(r'\D', '', phone)
        if len(digits) != 10 and not (len(digits) >= 10 and phone.startswith('+')):
            return None, "Please provide a valid 10-digit mobile number."
        normalized_phone = StaffService.normalize_phone(phone, country_code)

        if not department:
            return None, "Department is required."
        if department not in DEPARTMENT_DESIGNATIONS:
            return None, f"Invalid department '{department}'. Must be one of: {', '.join(DEPARTMENT_DESIGNATIONS.keys())}."

        if not designation:
            return None, "Designation is required."
        valid_designations = DEPARTMENT_DESIGNATIONS[department]
        if designation not in valid_designations:
            return None, f"Invalid designation '{designation}' for department '{department}'. Allowed options: {', '.join(valid_designations)}."

        # 2. Optional fields validation
        parsed_salary = None
        if salary:
            try:
                parsed_salary = float(salary)
                if parsed_salary < 0:
                    return None, "Monthly salary cannot be negative."
            except (ValueError, TypeError):
                return None, "Salary must be a valid number."

        parsed_joining_date = None
        if joining_date:
            try:
                parsed_joining_date = datetime.strptime(joining_date, '%Y-%m-%d').date()
            except ValueError:
                return None, "Joining Date must be in YYYY-MM-DD format."
        else:
            parsed_joining_date = datetime.utcnow().date()

        # 3. Map staff_type for legacy compatibility
        if department == 'Security':
            staff_type = 'Security'
        elif department == 'Other / General':
            staff_type = 'Other'
        else:
            staff_type = 'Maintenance'

        try:
            staff = Staff(
                full_name=full_name,
                phone=normalized_phone,
                department=department,
                designation=designation,
                staff_type=staff_type,
                salary=parsed_salary,
                joining_date=parsed_joining_date,
                is_active=True,
                user_id=None
            )
            db.session.add(staff)
            db.session.commit()
            return staff, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error saving staff member: {str(e)}"

    @staticmethod
    def update_staff(staff_id, full_name, phone, department, designation, salary=None, joining_date=None, is_active=None, country_code='+91'):
        staff = Staff.query.get(staff_id)
        if not staff:
            return False, "Staff member not found."

        full_name = (full_name or '').strip()
        phone = (phone or '').strip()
        department = (department or '').strip()
        designation = (designation or '').strip()

        if not full_name:
            return False, "Full Name is required."

        if not phone:
            return False, "Mobile Number is required."
        digits = re.sub(r'\D', '', phone)
        if len(digits) != 10 and not (len(digits) >= 10 and phone.startswith('+')):
            return False, "Please provide a valid 10-digit mobile number."
        normalized_phone = StaffService.normalize_phone(phone, country_code)

        if not department or department not in DEPARTMENT_DESIGNATIONS:
            return False, f"Invalid department '{department}'."

        if not designation or designation not in DEPARTMENT_DESIGNATIONS[department]:
            return False, f"Invalid designation '{designation}' for department '{department}'."

        parsed_salary = staff.salary
        if salary is not None and str(salary).strip() != '':
            try:
                parsed_salary = float(salary)
                if parsed_salary < 0:
                    return False, "Monthly salary cannot be negative."
            except (ValueError, TypeError):
                return False, "Salary must be a valid number."

        parsed_joining_date = staff.joining_date
        if joining_date:
            try:
                parsed_joining_date = datetime.strptime(joining_date, '%Y-%m-%d').date()
            except ValueError:
                return False, "Joining Date must be in YYYY-MM-DD format."

        # Map staff_type
        if department == 'Security':
            staff_type = 'Security'
        elif department == 'Other / General':
            staff_type = 'Other'
        else:
            staff_type = 'Maintenance'

        try:
            staff.full_name = full_name
            staff.phone = normalized_phone
            staff.department = department
            staff.designation = designation
            staff.staff_type = staff_type
            staff.salary = parsed_salary
            staff.joining_date = parsed_joining_date
            if is_active is not None:
                staff.is_active = bool(is_active)

            db.session.commit()
            return True, "Staff member updated successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating staff member: {str(e)}"

    @staticmethod
    def toggle_staff_status(staff_id):
        staff = Staff.query.get(staff_id)
        if not staff:
            return False, "Staff member not found."
        try:
            staff.is_active = not staff.is_active
            status_text = "Active" if staff.is_active else "Inactive"
            db.session.commit()
            return True, f"Staff member marked as {status_text}."
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def delete_staff(staff_id):
        staff = Staff.query.get(staff_id)
        if not staff:
            return False, "Staff member not found."

        # Prevent deletion if staff is referenced by existing complaints (Phase 6 requirement)
        assigned_count = Complaint.query.filter_by(assigned_to_staff_id=staff_id).count()
        if assigned_count > 0:
            return False, f"Cannot delete staff member with {assigned_count} linked complaint(s). Deactivate them instead to preserve historical records."

        try:
            user = staff.user
            db.session.delete(staff)
            if user:
                db.session.delete(user)
            db.session.commit()
            return True, "Staff member deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting staff member: {str(e)}"
