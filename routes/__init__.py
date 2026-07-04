from routes.home import home_bp
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.resident import resident_bp
from routes.visitor import visitor_bp
from routes.complaint import complaint_bp
from routes.maintenance import maintenance_bp
from routes.notice import notice_bp

__all__ = [
    'home_bp',
    'auth_bp',
    'dashboard_bp',
    'resident_bp',
    'visitor_bp',
    'complaint_bp',
    'maintenance_bp',
    'notice_bp'
]
