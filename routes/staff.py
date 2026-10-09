from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.staff_service import StaffService, DEPARTMENT_DESIGNATIONS

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/')
@login_required
@role_required('Admin')
def list_staff():
    staff_members = StaffService.get_all_staff()
    return render_template('staff/staff_list.html', staff_members=staff_members, departments=DEPARTMENT_DESIGNATIONS)

@staff_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_staff():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        department = request.form.get('department')
        designation = request.form.get('designation')
        salary = request.form.get('salary')
        joining_date = request.form.get('joining_date')

        staff, error = StaffService.create_staff(
            full_name=full_name,
            phone=phone,
            department=department,
            designation=designation,
            salary=salary,
            joining_date=joining_date,
            country_code=country_code
        )

        if error:
            flash(error, 'danger')
        else:
            flash(f"Staff member '{staff.name}' ({staff.designation}) registered successfully!", 'success')
            return redirect(url_for('staff.list_staff'))

    return render_template('staff/add_staff.html', departments=DEPARTMENT_DESIGNATIONS)

@staff_bp.route('/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_staff(staff_id):
    staff = StaffService.get_staff_by_id(staff_id)
    if not staff:
        flash("Staff member not found.", 'danger')
        return redirect(url_for('staff.list_staff'))

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        country_code = request.form.get('country_code', '+91')
        department = request.form.get('department')
        designation = request.form.get('designation')
        salary = request.form.get('salary')
        joining_date = request.form.get('joining_date')
        is_active = request.form.get('is_active') == '1'

        success, error = StaffService.update_staff(
            staff_id=staff_id,
            full_name=full_name,
            phone=phone,
            department=department,
            designation=designation,
            salary=salary,
            joining_date=joining_date,
            is_active=is_active,
            country_code=country_code
        )

        if not success:
            flash(error, 'danger')
        else:
            flash("Staff member updated successfully!", 'success')
            return redirect(url_for('staff.list_staff'))

    return render_template('staff/edit_staff.html', staff=staff, departments=DEPARTMENT_DESIGNATIONS)

@staff_bp.route('/toggle-status/<int:staff_id>', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_status(staff_id):
    success, message = StaffService.toggle_staff_status(staff_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('staff.list_staff'))

@staff_bp.route('/delete/<int:staff_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_staff(staff_id):
    success, error = StaffService.delete_staff(staff_id)
    if not success:
        flash(error, 'danger')
    else:
        flash("Staff member removed successfully.", 'success')
    return redirect(url_for('staff.list_staff'))
