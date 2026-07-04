from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import role_required
from models import db, Notice
from datetime import datetime

notice_bp = Blueprint('notice', __name__, url_prefix='/notice')

@notice_bp.route('/')
@login_required
def list_notices():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('notice/notices.html', notices=notices)

@notice_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_notice():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        expiry_date_str = request.form.get('expiry_date')
        
        expiry_date = None
        if expiry_date_str:
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()

        try:
            notice = Notice(
                title=title,
                content=content,
                created_by_user_id=current_user.id,
                expiry_date=expiry_date
            )
            db.session.add(notice)
            db.session.commit()
            flash("Notice published successfully!", 'success')
            return redirect(url_for('notice.list_notices'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error publishing notice: {str(e)}", 'danger')

    return render_template('notice/add_notice.html')

@notice_bp.route('/delete/<int:notice_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_notice(notice_id):
    notice = Notice.query.get(notice_id)
    if not notice:
        flash("Notice not found.", 'danger')
        return redirect(url_for('notice.list_notices'))
    
    try:
        db.session.delete(notice)
        db.session.commit()
        flash("Notice deleted successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting notice: {str(e)}", 'danger')
        
    return redirect(url_for('notice.list_notices'))
