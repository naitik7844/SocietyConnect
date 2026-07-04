import os
from flask import Flask, render_template
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

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure Upload Folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB tables if they don't exist (useful fallback, though init_db.py handles detailed seeding)
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Skipping auto db.create_all() since DB connection may need setup: {e}")

    app.run(host='0.0.0.0', port=5000)
