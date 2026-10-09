
from flask import Blueprint, render_template, redirect, url_for

from flask_login import login_required, current_user
from models import db, Resident, Visitor, Complaint, Notice, Vehicle, User, Flat, Maintenance, Building

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.is_admin:
        # Fetch Admin Stats
        pending_count = Complaint.query.filter(Complaint.status.in_(['Pending', 'Reopened'])).count()
        active_complaints = Complaint.query.filter(Complaint.status != 'Resolved').all()
        overdue_count = sum(1 for c in active_complaints if c.is_overdue)

        stats = {
            'total_residents': Resident.query.count(),
            'active_visitors': Visitor.query.filter_by(status='Checked-In').count(),
            'pending_complaints': pending_count,
            'overdue_complaints': overdue_count,
            'total_vehicles': Vehicle.query.count()
        }
        
        # Recent complaints, notices, visitor entries
        recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(5).all()
        recent_notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
        recent_visitors = Visitor.query.order_by(Visitor.check_in_time.desc()).limit(5).all()
        
        return render_template(
            'dashboard/admin_dashboard.html',
            stats=stats,
            recent_complaints=recent_complaints,
            recent_notices=recent_notices,
            recent_visitors=recent_visitors
        )

    elif current_user.is_security:
        # Security Guard Stats
        stats = {
            'active_visitors': Visitor.query.filter_by(status='Checked-In').count(),
            'total_today': Visitor.query.filter(
                db.func.date(Visitor.check_in_time) == db.func.current_date()
            ).count() if hasattr(db, 'func') else 0
        }
        
        active_visitors = Visitor.query.filter_by(status='Checked-In').order_by(Visitor.check_in_time.desc()).all()
        flats = Flat.query.all()
        buildings = Building.query.all()
        
        return render_template(
            'dashboard/security_dashboard.html',
            stats=stats,
            active_visitors=active_visitors,
            flats=flats,
            buildings=buildings
        )

    elif current_user.is_resident:
        # Resident stats (need to look up flat)
        resident = Resident.query.filter_by(user_id=current_user.id).first()
        if not resident:
            # Fallback if user is resident role but has no resident link
            return render_template('dashboard/resident_dashboard.html', stats={}, bills=[], complaints=[], notices=[])
            
        flat = resident.flat
        stats = {
            'flat_number': flat.flat_number,
            'building_name': flat.building.name,
            'occupancy_status': flat.occupancy_status,
            'unpaid_bills_count': Maintenance.query.filter_by(flat_id=flat.id, status='Unpaid').count(),
            'pending_complaints_count': Complaint.query.filter_by(flat_id=flat.id).filter(Complaint.status.in_(['Pending', 'Reopened'])).count()
        }
        
        bills = Maintenance.query.filter_by(flat_id=flat.id).order_by(Maintenance.due_date.desc()).all()
        complaints = Complaint.query.filter_by(flat_id=flat.id).order_by(Complaint.created_at.desc()).all()
        notices = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
        
        return render_template(
            'dashboard/resident_dashboard.html',
            stats=stats,
            bills=bills,
            complaints=complaints,
            notices=notices
        )

    elif current_user.role and current_user.role.name == 'Staff':
        return redirect(url_for('complaint.list_complaints'))

    return redirect(url_for('auth.login'))
