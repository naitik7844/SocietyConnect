from models import db, Vehicle, Flat, Building

class VehicleService:
    @staticmethod
    def get_all_vehicles():
        return Vehicle.query.order_by(Vehicle.id.desc()).all()

    @staticmethod
    def get_vehicle_by_id(vehicle_id):
        return Vehicle.query.get(vehicle_id)

    @staticmethod
    def search_vehicles(search_query):
        if not search_query:
            return Vehicle.query.order_by(Vehicle.id.desc()).all()
        search_pattern = f"%{search_query}%"
        return Vehicle.query.join(Flat).outerjoin(Building).filter(
            db.or_(
                Vehicle.vehicle_number.like(search_pattern),
                Vehicle.owner_name.like(search_pattern),
                Vehicle.vehicle_type.like(search_pattern),
                Flat.flat_number.like(search_pattern),
                Building.name.like(search_pattern)
            )
        ).order_by(Vehicle.id.desc()).all()

    @staticmethod
    def create_vehicle(flat_id, vehicle_type, vehicle_number, owner_name):
        if not flat_id:
            return None, "Please select an assigned flat."
        if not vehicle_number or not vehicle_number.strip():
            return None, "Vehicle registration number is required."
        if not owner_name or not owner_name.strip():
            return None, "Owner name is required."

        clean_number = vehicle_number.strip().upper()
        existing = Vehicle.query.filter_by(vehicle_number=clean_number).first()
        if existing:
            return None, f"Vehicle with number '{clean_number}' is already registered."

        try:
            vehicle = Vehicle(
                flat_id=flat_id,
                vehicle_type=vehicle_type or '4 Wheeler',
                vehicle_number=clean_number,
                owner_name=owner_name.strip()
            )
            db.session.add(vehicle)
            db.session.commit()
            return vehicle, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def update_vehicle(vehicle_id, flat_id, vehicle_type, vehicle_number, owner_name):
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."

        if not flat_id:
            return False, "Please select an assigned flat."
        if not vehicle_number or not vehicle_number.strip():
            return False, "Vehicle registration number is required."
        if not owner_name or not owner_name.strip():
            return False, "Owner name is required."

        clean_number = vehicle_number.strip().upper()
        existing = Vehicle.query.filter(Vehicle.vehicle_number == clean_number, Vehicle.id != vehicle_id).first()
        if existing:
            return False, f"Vehicle with number '{clean_number}' is already registered."

        try:
            vehicle.flat_id = flat_id
            vehicle.vehicle_type = vehicle_type or '4 Wheeler'
            vehicle.vehicle_number = clean_number
            vehicle.owner_name = owner_name.strip()
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @staticmethod
    def delete_vehicle(vehicle_id):
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            return False, "Vehicle not found."
        try:
            db.session.delete(vehicle)
            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)
