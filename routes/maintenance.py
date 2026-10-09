from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.maintenance_service import MaintenanceService
from services.payment_service import PaymentService
from models import Flat, Building, Resident, Maintenance

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

@maintenance_bp.route('/')
@login_required
def list_bills():
    status = request.args.get('status')
    if current_user.is_admin:
        if status:
            bills = Maintenance.query.filter_by(status=status).order_by(Maintenance.due_date.desc()).all()
        else:
            bills = MaintenanceService.get_all_bills()
        buildings = Building.query.all()
        flats = Flat.query.all()
        return render_template('maintenance/maintenance.html', bills=bills, buildings=buildings, flats=flats, current_status=status)
    else:
        resident = Resident.query.filter_by(user_id=current_user.id).first()
        if not resident:
            flash("No flat associated with your resident profile.", 'warning')
            return redirect(url_for('dashboard.index'))
        if status:
            bills = Maintenance.query.filter_by(flat_id=resident.flat_id, status=status).order_by(Maintenance.due_date.desc()).all()
        else:
            bills = MaintenanceService.get_bills_by_flat(resident.flat_id)
        return render_template('maintenance/maintenance.html', bills=bills, current_status=status)

@maintenance_bp.route('/add_bill', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_bill():
    flats = Flat.query.all()
    buildings = Building.query.all()
    
    flats_data = []
    for flat in flats:
        res_names = ", ".join([r.user.username for r in flat.residents if r.user]) if flat.residents else "Vacant"
        flats_data.append({
            'id': flat.id,
            'flat_number': flat.flat_number,
            'building_name': flat.building.name if flat.building else '',
            'resident_name': res_names
        })

    if request.method == 'POST':
        bill_type = request.form.get('bill_type')  # Individual or Bulk
        title = request.form.get('title')
        amount = float(request.form.get('amount'))
        due_date = request.form.get('due_date')
        
        if bill_type == 'Individual':
            flat_id = request.form.get('flat_id')
            bill, error = MaintenanceService.generate_bill(
                flat_id=int(flat_id),
                title=title,
                amount=amount,
                due_date=due_date
            )
            if error:
                flash(error, 'danger')
            else:
                flash("Maintenance bill generated successfully!", 'success')
        else:
            # Bulk bill per Building
            building_id = request.form.get('building_id')
            count, error = MaintenanceService.generate_bulk_bills(
                building_id=int(building_id),
                title=title,
                amount=amount,
                due_date=due_date
            )
            if error:
                flash(error, 'danger')
            else:
                flash(f"Successfully generated {count} bills for the selected building.", 'success')
        
        return redirect(url_for('maintenance.list_bills'))

    return render_template('maintenance/add_bill.html', flats=flats, buildings=buildings, flats_data=flats_data)


@maintenance_bp.route('/pay/<int:bill_id>', methods=['POST'])
@login_required
def pay_bill(bill_id):
    bill = MaintenanceService.get_bill_by_id(bill_id)
    if not bill:
        flash("Bill not found.", 'danger')
        return redirect(url_for('dashboard.index'))

    # Verify authorization
    if not current_user.is_admin:
        resident = Resident.query.filter_by(user_id=current_user.id).first()
        if not resident or resident.flat_id != bill.flat_id:
            flash("You are not authorized to pay this bill.", 'danger')
            return redirect(url_for('dashboard.index'))

    payment_method = request.form.get('payment_method', 'Card')
    
    payment, error = PaymentService.process_payment(
        maintenance_id=bill_id,
        payment_method=payment_method,
        amount_paid=bill.amount
    )

    if error:
        flash(error, 'danger')
    else:
        flash(f"Payment of ${bill.amount} processed successfully! Transaction: {payment.transaction_id}", 'success')

    return redirect(url_for('dashboard.index'))
