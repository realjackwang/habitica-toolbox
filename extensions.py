from flask_admin import Admin
from flask_babel import Babel
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
admin = Admin()
babel = Babel()
migrate = Migrate()
bootstrap = Bootstrap()
login_manager = LoginManager()
