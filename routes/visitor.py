from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.visitor_service import VisitorService
from models import Flat, Building

visitor_bp = Blueprint('visitor', __name__, url_prefix='/visitor')

@visitor_bp.route('/')
@login_required
@role_required('Admin', 'Security')
def list_visitors():
    status = request.args.get('status')
    if status == 'Checked-In':
        visitors = VisitorService.get_active_visitors()
    else:
        visitors = VisitorService.get_all_visitors()
    return render_template('visitor/visitors.html', visitors=visitors, current_status=status)

@visitor_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Security')
def add_visitor():
    flats = Flat.query.all()
    buildings = Building.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        full_phone = f"{country_code}{phone}"
        purpose = request.form.get('purpose')
        flat_id = request.form.get('flat_id')
        vehicle_number = request.form.get('vehicle_number')

        visitor, error = VisitorService.log_visitor_entry(
            name=name,
            phone=full_phone,
            purpose=purpose,
            flat_id=int(flat_id),
            vehicle_number=vehicle_number,
            checked_in_by=current_user.id
        )

        if error:
            flash(error, 'danger')
        else:
            flash("Visitor entry logged successfully!", 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('visitor/add_visitor.html', flats=flats, buildings=buildings)

@visitor_bp.route('/checkout/<int:visitor_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Security')
def checkout_visitor(visitor_id):
    success, error = VisitorService.log_visitor_checkout(visitor_id)
    if not success:
        flash(error, 'danger')
    else:
        flash("Visitor checked out successfully.", 'success')
    return redirect(url_for('dashboard.index'))
