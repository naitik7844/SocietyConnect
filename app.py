import os
import tempfile
from flask import Flask, render_template, send_from_directory
from flask_login import LoginManager
from config import Config
from models.db import db
from models.user import User

# Import Blueprints
from routes.home import home_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.resident import resident_bp
from routes.visitor import visitor_bp
from routes.complaint import complaint_bp
from routes.maintenance import maintenance_bp
from routes.notice import notice_bp
from routes.vehicle import vehicle_bp
from routes.staff import staff_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure Upload Folder exists safely without failing on read-only filesystems (e.g., Vercel /var/task)
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        try:
            os.makedirs(upload_folder, exist_ok=True)
        except (OSError, PermissionError) as e:
            # Fallback to temp directory if specified location is read-only
            fallback_dir = os.path.join(tempfile.gettempdir(), 'society_connect_uploads')
            try:
                os.makedirs(fallback_dir, exist_ok=True)
                app.config['UPLOAD_FOLDER'] = fallback_dir
            except Exception as fb_err:
                app.logger.warning(
                    f"Unable to create upload folder '{upload_folder}': {e}. "
                    f"Fallback to '{fallback_dir}' also failed: {fb_err}"
                )
                app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

    # Initialize extensions
    db.init_app(app)

    # Configure Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(visitor_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(notice_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(staff_bp)

    # Error Handlers
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    # Route for serving uploaded files (supports local static/uploads and temporary uploads)
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        folder = app.config.get('UPLOAD_FOLDER')
        if folder and os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename)
        static_uploads = os.path.join(app.root_path, 'static', 'uploads')
        if os.path.exists(os.path.join(static_uploads, filename)):
            return send_from_directory(static_uploads, filename)
        return render_template('errors/404.html'), 404

    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB tables if they don't exist (useful fallback, though init_db.py handles detailed seeding)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Skipping auto db.create_all() since DB connection may need setup: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)
