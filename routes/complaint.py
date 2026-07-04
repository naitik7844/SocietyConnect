from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.complaint_service import ComplaintService
from models import Resident, Staff

complaint_bp = Blueprint('complaint', __name__, url_prefix='/complaint')

@complaint_bp.route('/')
@login_required
def list_complaints():
    if current_user.is_admin:
        complaints = ComplaintService.get_all_complaints()
        staff_members = ComplaintService.get_maintenance_staff()
        return render_template('complaint/complaints.html', complaints=complaints, staff_members=staff_members)
    else:
        complaints = ComplaintService.get_complaints_by_user(current_user.id)
        return render_template('complaint/complaints.html', complaints=complaints)

@complaint_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Resident', 'Owner')
def add_complaint():
    resident = Resident.query.filter_by(user_id=current_user.id).first()
    if not resident:
        flash("You are not registered to a flat to file a complaint.", 'danger')
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        complaint, error = ComplaintService.file_complaint(
            title=title,
            description=description,
            category=category,
            flat_id=resident.flat_id,
            created_by_user_id=current_user.id
        )

        if error:
            flash(error, 'danger')
        else:
            flash("Complaint submitted successfully!", 'success')
            return redirect(url_for('dashboard.index'))

    return render_template('complaint/add_complaint.html')

@complaint_bp.route('/assign/<int:complaint_id>', methods=['POST'])
@login_required
@role_required('Admin')
def assign_complaint(complaint_id):
    staff_id = request.form.get('staff_id')
    if not staff_id:
        flash("Please select a staff member.", 'warning')
        return redirect(url_for('complaint.list_complaints'))

    success, error = ComplaintService.assign_complaint(complaint_id, int(staff_id))
    if not success:
        flash(error, 'danger')
    else:
        flash("Complaint assigned to maintenance staff successfully.", 'success')
    return redirect(url_for('complaint.list_complaints'))

@complaint_bp.route('/resolve/<int:complaint_id>', methods=['POST'])
@login_required
def resolve_complaint(complaint_id):
    resolution_notes = request.form.get('resolution_notes')
    
    # Check authorization (Only Admin or assigned Staff can resolve)
    complaint = ComplaintService.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", 'danger')
        return redirect(url_for('dashboard.index'))

    is_authorized = current_user.is_admin
    if not is_authorized and current_user.staff:
        is_authorized = complaint.assigned_to_staff_id == current_user.staff.id

    if not is_authorized:
        flash("You are not authorized to resolve this complaint.", 'danger')
        return redirect(url_for('dashboard.index'))

    success, error = ComplaintService.resolve_complaint(complaint_id, resolution_notes)
    if not success:
        flash(error, 'danger')
    else:
        flash("Complaint resolved successfully.", 'success')

    if current_user.is_admin:
        return redirect(url_for('complaint.list_complaints'))
    return redirect(url_for('dashboard.index'))
