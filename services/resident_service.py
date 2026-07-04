from models import db, Resident, User, Flat, Building, Role
from utils.validators import validate_phone

class ResidentService:
    @staticmethod
    def get_all_residents():
        return Resident.query.all()

    @staticmethod
    def search_residents(search_query):
        if not search_query:
            return Resident.query.all()
        search_pattern = f"%{search_query}%"
        return Resident.query.join(User).outerjoin(Flat).filter(
            db.or_(
                User.username.like(search_pattern),
                User.email.like(search_pattern),
                User.phone.like(search_pattern),
                Resident.resident_type.like(search_pattern),
                Flat.flat_number.like(search_pattern)
            )
        ).all()


    @staticmethod
    def get_resident_by_id(resident_id):
        return Resident.query.get(resident_id)

    @staticmethod
    def get_resident_by_user_id(user_id):
        return Resident.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create_resident(username, email, phone, password, flat_id, resident_type, emergency_contact=None, status='Active'):
        # Check if phone number is valid
        if not validate_phone(phone):
            return None, "Invalid phone number. Must include a country code and 10 digits."

        # Check if username or email exists
        if User.query.filter_by(username=username).first():
            return None, "Username already exists"
        if User.query.filter_by(email=email).first():
            return None, "Email already exists"

        role_name = 'Owner' if resident_type == 'Owner' else 'Resident'
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role.query.filter_by(name='Resident').first()

        try:
            user = User(
                username=username,
                email=email,
                phone=phone,
                role_id=role.id,
                status=status
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            resident = Resident(
                user_id=user.id,
                flat_id=flat_id,
                resident_type=resident_type,
                emergency_contact=emergency_contact
            )
            db.session.add(resident)
            
            # Update Flat occupancy status if it was vacant
            if flat_id:
                flat = Flat.query.get(flat_id)
                if flat and flat.occupancy_status == 'Vacant':
                    flat.occupancy_status = f"{resident_type}-Occupied"

            db.session.commit()
            return resident, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_resident(resident_id, email, phone, flat_id, resident_type, emergency_contact, status):
        resident = Resident.query.get(resident_id)
        if not resident:
            return False, "Resident not found"
        
        # Check if phone number is valid
        if not validate_phone(phone):
            return False, "Invalid phone number. Must include a country code and 10 digits."
        
        try:
            user = resident.user
            user.email = email
            user.phone = phone
            user.status = status
            
            # Handle flat change
            old_flat_id = resident.flat_id
            resident.flat_id = flat_id
            resident.resident_type = resident_type
            resident.emergency_contact = emergency_contact
            
            # Update old flat status if empty now
            if old_flat_id != flat_id:
                if old_flat_id:
                    old_flat = Flat.query.get(old_flat_id)
                    if old_flat and len(old_flat.residents) <= 1:
                        old_flat.occupancy_status = 'Vacant'
                
                if flat_id:
                    new_flat = Flat.query.get(flat_id)
                    if new_flat:
                        new_flat.occupancy_status = f"{resident_type}-Occupied"

            db.session.commit()
            return True, "Resident updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def delete_resident(resident_id):
        resident = Resident.query.get(resident_id)
        if not resident:
            return False, "Resident not found"
        try:
            user = resident.user
            flat = resident.flat
            db.session.delete(resident)
            if user:
                db.session.delete(user)
            
            # Check if flat is empty
            if flat and len(flat.residents) == 0:
                flat.occupancy_status = 'Vacant'
                
            db.session.commit()
            return True, "Resident deleted successfully"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def get_all_flats_grouped_by_building():
        buildings = Building.query.all()
        result = {}
        for b in buildings:
            result[b.name] = Flat.query.filter_by(building_id=b.id).all()
        return result
