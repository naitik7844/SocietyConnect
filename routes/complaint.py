from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from utils.decorators import role_required
from services.complaint_service import ComplaintService
from models import Resident, Staff, Complaint

complaint_bp = Blueprint('complaint', __name__, url_prefix='/complaint')

@complaint_bp.route('/')
@login_required
def list_complaints():
    status = request.args.get('status')
    if current_user.is_admin:
        complaints = ComplaintService.get_all_complaints(status=status)
        # Fetch strictly category-eligible staff for each complaint
        staff_by_complaint = {c.id: ComplaintService.get_staff_for_complaint(c.category) for c in complaints}
        return render_template(
            'complaint/complaints.html',
            complaints=complaints,
            staff_by_complaint=staff_by_complaint,
            current_status=status
        )
    else:
        complaints = ComplaintService.get_complaints_by_user(current_user.id, status=status)
        return render_template('complaint/complaints.html', complaints=complaints, current_status=status)

@complaint_bp.route('/<int:complaint_id>')
@complaint_bp.route('/view/<int:complaint_id>')
@login_required
def view_complaint(complaint_id):
    complaint = ComplaintService.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint ticket not found.", 'danger')
        return redirect(url_for('complaint.list_complaints'))

    # Strict privacy and ownership enforcement
    if not ComplaintService.can_user_view_complaint(complaint, current_user):
        flash("You are not authorized to view this complaint ticket or staff contact details.", 'danger')
        return redirect(url_for('complaint.list_complaints')), 403

    eligible_info = None
    if current_user.is_admin:
        eligible_info = ComplaintService.get_staff_for_complaint(complaint.category)

    return render_template(
        'complaint/complaint_detail.html',
        complaint=complaint,
        eligible_info=eligible_info
    )

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
            flash("Complaint ticket submitted successfully!", 'success')
            return redirect(url_for('complaint.view_complaint', complaint_id=complaint.id))

    return render_template('complaint/add_complaint.html')

@complaint_bp.route('/assign/<int:complaint_id>', methods=['POST'])
@login_required
@role_required('Admin')
def assign_complaint(complaint_id):
    staff_id = request.form.get('staff_id')
    if not staff_id:
        flash("Please select an eligible staff member.", 'warning')
        return redirect(request.referrer or url_for('complaint.list_complaints'))

    try:
        parsed_staff_id = int(staff_id)
    except (ValueError, TypeError):
        flash("Invalid staff selection.", 'warning')
        return redirect(request.referrer or url_for('complaint.list_complaints'))

    success, message = ComplaintService.assign_complaint(complaint_id, parsed_staff_id, admin_user_id=current_user.id)
    if not success:
        flash(message, 'danger')
    else:
        flash(message, 'success')

    next_url = request.form.get('next') or request.referrer or url_for('complaint.list_complaints')
    return redirect(next_url)

@complaint_bp.route('/start/<int:complaint_id>', methods=['POST'])
@login_required
@role_required('Admin')
def start_complaint(complaint_id):
    notes = request.form.get('notes')
    success, message = ComplaintService.mark_in_progress(complaint_id, admin_user_id=current_user.id, notes=notes)
    if not success:
        flash(message, 'danger')
    else:
        flash(message, 'success')

    next_url = request.form.get('next') or request.referrer or url_for('complaint.list_complaints')
    return redirect(next_url)

@complaint_bp.route('/resolve/<int:complaint_id>', methods=['POST'])
@login_required
def resolve_complaint(complaint_id):
    complaint = ComplaintService.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint not found.", 'danger')
        return redirect(url_for('complaint.list_complaints'))

    # Strict authorization: Only Admin or authorized owner/tenant for this complaint
    if not ComplaintService.can_user_manage_complaint(complaint, current_user):
        flash("You are not authorized to resolve this complaint.", 'danger')
        return redirect(url_for('complaint.list_complaints')), 403

    resolution_notes = request.form.get('resolution_notes')
    success, message = ComplaintService.resolve_complaint(complaint_id, resolution_notes, resolved_by_user_id=current_user.id)
    if not success:
        flash(message, 'danger')
    else:
        flash(message, 'success')

    next_url = request.form.get('next') or request.referrer or url_for('complaint.view_complaint', complaint_id=complaint.id)
    return redirect(next_url)

@complaint_bp.route('/reopen/<int:complaint_id>', methods=['POST'])
@login_required
def reopen_complaint(complaint_id):
    complaint = ComplaintService.get_complaint_by_id(complaint_id)
    if not complaint:
        flash("Complaint ticket not found.", 'danger')
        return redirect(url_for('complaint.list_complaints'))

    # Verify authorization (Admin or authorized resident/owner)
    if not ComplaintService.can_user_view_complaint(complaint, current_user):
        flash("You are not authorized to reopen this complaint.", 'danger')
        return redirect(url_for('complaint.list_complaints')), 403

    reason = request.form.get('reason')
    success, message = ComplaintService.reopen_complaint(complaint_id, reason=reason, user_id=current_user.id)
    if not success:
        flash(message, 'danger')
    else:
        flash(message, 'success')

    next_url = request.form.get('next') or request.referrer or url_for('complaint.view_complaint', complaint_id=complaint.id)
    return redirect(next_url)
