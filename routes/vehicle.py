from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from utils.decorators import role_required
from services.vehicle_service import VehicleService
from models import Flat, Building

vehicle_bp = Blueprint('vehicle', __name__, url_prefix='/vehicle')

@vehicle_bp.route('/')
@login_required
@role_required('Admin', 'Security')
def list_vehicles():
    q = request.args.get('q', '').strip()
    if q:
        vehicles = VehicleService.search_vehicles(q)
    else:
        vehicles = VehicleService.get_all_vehicles()
    return render_template('vehicle/vehicles.html', vehicles=vehicles, search_query=q)

@vehicle_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_vehicle():
    flats = Flat.query.all()
    buildings = Building.query.all()
    if request.method == 'POST':
        flat_id = request.form.get('flat_id')
        vehicle_type = request.form.get('vehicle_type', '4 Wheeler')
        vehicle_number = request.form.get('vehicle_number')
        owner_name = request.form.get('owner_name')

        parsed_flat_id = int(flat_id) if flat_id else None
        vehicle, error = VehicleService.create_vehicle(
            flat_id=parsed_flat_id,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            owner_name=owner_name
        )

        if error:
            flash(error, 'danger')
        else:
            flash("Vehicle registered successfully!", 'success')
            return redirect(url_for('vehicle.list_vehicles'))

    return render_template('vehicle/add_vehicle.html', flats=flats, buildings=buildings)

@vehicle_bp.route('/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_vehicle(vehicle_id):
    vehicle = VehicleService.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        flash("Vehicle record not found.", 'danger')
        return redirect(url_for('vehicle.list_vehicles'))

    flats = Flat.query.all()
    buildings = Building.query.all()
    if request.method == 'POST':
        flat_id = request.form.get('flat_id')
        vehicle_type = request.form.get('vehicle_type', '4 Wheeler')
        vehicle_number = request.form.get('vehicle_number')
        owner_name = request.form.get('owner_name')

        parsed_flat_id = int(flat_id) if flat_id else None
        success, error = VehicleService.update_vehicle(
            vehicle_id=vehicle_id,
            flat_id=parsed_flat_id,
            vehicle_type=vehicle_type,
            vehicle_number=vehicle_number,
            owner_name=owner_name
        )

        if not success:
            flash(error, 'danger')
        else:
            flash("Vehicle details updated successfully!", 'success')
            return redirect(url_for('vehicle.list_vehicles'))

    return render_template('vehicle/update_vehicle.html', vehicle=vehicle, flats=flats, buildings=buildings)

@vehicle_bp.route('/delete/<int:vehicle_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_vehicle(vehicle_id):
    success, error = VehicleService.delete_vehicle(vehicle_id)
    if not success:
        flash(error, 'danger')
    else:
        flash("Vehicle deregistered successfully.", 'success')
    return redirect(url_for('vehicle.list_vehicles'))
