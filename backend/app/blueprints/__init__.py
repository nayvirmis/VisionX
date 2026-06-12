from .auth import bp as auth_bp
from .feeds import bp as feeds_bp
from .health import bp as health_bp
from .maintenance import bp as maintenance_bp
from .shares import bp as shares_bp
from .x_accounts import bp as x_accounts_bp

ALL_BLUEPRINTS = (
    health_bp,
    auth_bp,
    x_accounts_bp,
    shares_bp,
    feeds_bp,
    maintenance_bp,
)
