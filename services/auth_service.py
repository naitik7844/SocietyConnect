from models import db, User, Role
from flask_login import login_user, logout_user
from utils.validators import validate_phone

class AuthService:
    @staticmethod
    def load_user(user_id):
        return User.query.get(int(user_id))

    @staticmethod
    def authenticate_user(username, password):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if user.status != 'Active':
                return None, "Your account is not active. Please contact administrator."
            return user, None
        return None, "Invalid username or password"

    @staticmethod
    def register_resident(username, email, password, phone, flat_id=None, resident_type='Tenant', emergency_contact=None):
        # Check if phone number is valid
        if not validate_phone(phone):
            return None, "Invalid phone number. Must include a country code and 10 digits."

        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        if User.query.filter_by(email=email).first():
            return None, "Email already exists"

        # Get role ID for Resident/Owner
        role_name = 'Owner' if resident_type == 'Owner' else 'Resident'
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            # Fallback to Resident role
            role = Role.query.filter_by(name='Resident').first()

        try:
            # Create user
            user = User(
                username=username,
                email=email,
                phone=phone,
                role_id=role.id,
                status='Pending'  # Pending admin approval
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Get user ID

            # Create resident link
            from models import Resident
            resident = Resident(
                user_id=user.id,
                flat_id=flat_id,
                resident_type=resident_type,
                emergency_contact=emergency_contact
            )
            db.session.add(resident)
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error during registration: {str(e)}"
            
    @staticmethod
    def change_password(user, current_password, new_password):
        if not user.check_password(current_password):
            return False, "Current password is incorrect"
        try:
            user.set_password(new_password)
            db.session.commit()
            return True, "Password updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating password: {str(e)}"
