from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from utils.decorators import role_required
from utils.validators import split_phone
from services.resident_service import ResidentService
from models import Flat, Building

resident_bp = Blueprint('resident', __name__, url_prefix='/resident')

@resident_bp.route('/')
@login_required
@role_required('Admin')
def list_residents():
    q = request.args.get('q', '').strip()
    if q:
        residents = ResidentService.search_residents(q)
    else:
        residents = ResidentService.get_all_residents()
    return render_template('resident/residents.html', residents=residents, search_query=q)


@resident_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_resident():
    flats = Flat.query.all()
    buildings = Building.query.all()
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        full_phone = f"{country_code}{phone}"
        password = request.form.get('password')
        flat_id = request.form.get('flat_id')
        resident_type = request.form.get('resident_type')
        emergency_contact = request.form.get('emergency_contact')

        parsed_flat_id = int(flat_id) if flat_id else None
        resident, error = ResidentService.create_resident(
            username=username,
            email=email,
            phone=full_phone,
            password=password,
            flat_id=parsed_flat_id,
            resident_type=resident_type,
            emergency_contact=emergency_contact
        )

        if error:
            flash(error, 'danger')
        else:
            flash("Resident added successfully!", 'success')
            return redirect(url_for('resident.list_residents'))

    return render_template('resident/add_resident.html', flats=flats, buildings=buildings)

@resident_bp.route('/edit/<int:resident_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_resident(resident_id):
    resident = ResidentService.get_resident_by_id(resident_id)
    if not resident:
        flash("Resident not found.", 'danger')
        return redirect(url_for('resident.list_residents'))

    flats = Flat.query.all()
    buildings = Building.query.all()
    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        full_phone = f"{country_code}{phone}"
        flat_id = request.form.get('flat_id')
        resident_type = request.form.get('resident_type')
        emergency_contact = request.form.get('emergency_contact')
        status = request.form.get('status')

        parsed_flat_id = int(flat_id) if flat_id else None
        success, error = ResidentService.update_resident(
            resident_id=resident_id,
            email=email,
            phone=full_phone,
            flat_id=parsed_flat_id,
            resident_type=resident_type,
            emergency_contact=emergency_contact,
            status=status
        )

        if not success:
            flash(error, 'danger')
        else:
            flash("Resident details updated successfully!", 'success')
            return redirect(url_for('resident.list_residents'))

    # Split resident's phone number into country code and local number for the view
    cur_country_code, cur_local_phone = split_phone(resident.user.phone)
    
    return render_template(
        'resident/update_resident.html',
        resident=resident,
        flats=flats,
        buildings=buildings,
        country_code=cur_country_code,
        phone_number=cur_local_phone
    )

@resident_bp.route('/delete/<int:resident_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_resident(resident_id):
    success, error = ResidentService.delete_resident(resident_id)
    if not success:
        flash(error, 'danger')
    else:
        flash("Resident deleted successfully.", 'success')
    return redirect(url_for('resident.list_residents'))
