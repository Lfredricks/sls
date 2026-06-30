from flask_login import LoginManager
from flask_wtf import CSRFProtect

login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'admin.login'
login_manager.login_message_category = 'info'
